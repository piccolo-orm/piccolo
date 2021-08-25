from __future__ import annotations

import dataclasses
import typing as t

import black
from typing_extensions import Literal

from piccolo.columns.base import Column
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    BigInt,
    Boolean,
    Bytea,
    Date,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    Real,
    Serial,
    SmallInt,
    Text,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.engine.finder import engine_finder
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table, create_table_class
from piccolo.utils.naming import _snake_to_camel

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.engine.base import Engine


class ForeignKeyPlaceholder(Table):
    pass


@dataclasses.dataclass
class RowMeta:
    column_default: str
    column_name: str
    is_nullable: Literal["YES", "NO"]
    table_name: str
    character_maximum_length: t.Optional[int]
    data_type: str

    @classmethod
    def get_column_name_str(cls) -> str:
        return ", ".join([i.name for i in dataclasses.fields(cls)])


@dataclasses.dataclass
class Constraint:
    constraint_type: Literal["PRIMARY KEY", "UNIQUE", "FOREIGN KEY", "CHECK"]
    constraint_name: str
    column_name: t.Optional[str] = None


@dataclasses.dataclass
class TableConstraints:
    """
    All of the constraints for a certain table in the database.
    """

    tablename: str
    constraints: t.List[Constraint]

    def __post_init__(self):
        foreign_key_constraints: t.List[Constraint] = []
        unique_constraints: t.List[Constraint] = []
        primary_key_constraints: t.List[Constraint] = []

        for constraint in self.constraints:
            if constraint.constraint_type == "FOREIGN KEY":
                foreign_key_constraints.append(constraint)
            elif constraint.constraint_type == "PRIMARY KEY":
                primary_key_constraints.append(constraint)
            elif constraint.constraint_type == "UNIQUE":
                unique_constraints.append(constraint)

        self.foreign_key_constraints = foreign_key_constraints
        self.unique_constraints = unique_constraints
        self.primary_key_constraints = primary_key_constraints

    def is_primary_key(self, column_name: str) -> bool:
        for i in self.primary_key_constraints:
            if i.column_name == column_name:
                return True
        return False

    def is_unique(self, column_name: str) -> bool:
        for i in self.unique_constraints:
            if i.column_name == column_name:
                return True
        return False

    def is_foreign_key(self, column_name: str) -> bool:
        for i in self.foreign_key_constraints:
            if i.column_name == column_name:
                return True
        return False

    def get_foreign_key_constraint_name(self, column_name) -> str:
        for i in self.foreign_key_constraints:
            if i.column_name == column_name:
                return i.constraint_name

        raise ValueError("No matching constraint found")


@dataclasses.dataclass
class OutputSchema:
    """
    Represents the schema which will be printed out.

    :param imports:
        e.g. ["from piccolo.table import Table"]
    :param warnings:
        e.g. ["some_table.some_column unrecognised_type"]
    :param tables:
        e.g. ["class MyTable(Table): ..."]

    """

    imports: t.List[str]
    warnings: t.List[str]
    tables: t.List[t.Type[Table]]

    def get_table_with_name(self, name: str) -> t.Optional[t.Type[Table]]:
        """
        Just used by unit tests.
        """
        try:
            return next(
                table for table in self.tables if table.__name__ == name
            )
        except StopIteration:
            return None


COLUMN_TYPE_MAP = {
    "bigint": BigInt,
    "boolean": Boolean,
    "bytea": Bytea,
    "character varying": Varchar,
    "date": Date,
    "integer": Integer,
    "interval": Interval,
    "json": JSON,
    "jsonb": JSONB,
    "numeric": Numeric,
    "real": Real,
    "smallint": SmallInt,
    "text": Text,
    "timestamp with time zone": Timestamptz,
    "timestamp without time zone": Timestamp,
    "uuid": UUID,
}


async def get_contraints(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> TableConstraints:
    """
    Get all of the constraints for a table.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.

    """
    constraints = await table_class.raw(
        (
            "SELECT tc.constraint_name, tc.constraint_type, kcu.column_name "  # noqa: E501
            "FROM information_schema.table_constraints tc "
            "LEFT JOIN information_schema.key_column_usage kcu "
            "ON tc.constraint_name = kcu.constraint_name "
            "WHERE tc.table_schema = {} "
            "AND tc.table_name = {} "
        ),
        schema_name,
        tablename,
    )
    return TableConstraints(
        tablename=tablename,
        constraints=[Constraint(**i) for i in constraints],
    )


async def get_tablenames(
    table_class: t.Type[Table], schema_name: str = "public"
) -> t.List[str]:
    """
    Get the tablenames for the schema.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.
    :returns:
        A list of tablenames for the given schema.

    """
    tablenames: t.List[str] = [
        i["tablename"]
        for i in await table_class.raw(
            (
                "SELECT tablename FROM pg_catalog.pg_tables WHERE "
                "schemaname = {}"
            ),
            schema_name,
        ).run()
    ]
    return tablenames


async def get_table_schema(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> t.List[RowMeta]:
    """
    Get the schema from the database.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.
    :param tablename:
        The name of the table whose schema we want from the database.
    :param schema_name:
        A Postgres database can have multiple schemas, this is the name of the
        one you're interested in.
    :returns:
        A list, with each item containing information about a column in the
        table.

    """
    row_meta_list = await table_class.raw(
        (
            f"SELECT {RowMeta.get_column_name_str()} FROM "
            "information_schema.columns "
            "WHERE table_schema = {} "
            "AND table_name = {}"
        ),
        schema_name,
        tablename,
    ).run()
    return [RowMeta(**row_meta) for row_meta in row_meta_list]


async def get_foreign_key_reference(
    table_class: t.Type[Table], constraint_name: str
) -> t.Optional[str]:
    """
    Retrieve the name of the table that a foreign key is referencing.
    """
    response = await table_class.raw(
        (
            "SELECT table_name "
            "FROM information_schema.constraint_column_usage "
            "WHERE constraint_name = {};"
        ),
        constraint_name,
    )
    if len(response) > 0:
        return response[0]["table_name"]
    else:
        return None


async def get_output_schema(schema_name: str = "public") -> OutputSchema:
    engine: t.Optional[Engine] = engine_finder()

    if engine is None:
        raise ValueError(
            "Unable to find the engine - make sure piccolo_conf is on the "
            "path."
        )

    if not isinstance(engine, PostgresEngine):
        raise ValueError(
            "This feature is currently only supported in Postgres."
        )

    class Schema(Table, db=engine):
        """
        Just used for making raw queries on the db.
        """

        pass

    tablenames = await get_tablenames(Schema, schema_name=schema_name)

    tables: t.List[t.Type[Table]] = []
    imports: t.Set[str] = {"from piccolo.table import Table"}
    warnings: t.List[str] = []

    for tablename in tablenames:
        constraints = await get_contraints(
            table_class=Schema, tablename=tablename, schema_name=schema_name
        )
        table_schema = await get_table_schema(
            table_class=Schema, tablename=tablename, schema_name=schema_name
        )

        columns: t.Dict[str, Column] = {}

        for pg_row_meta in table_schema:
            data_type = pg_row_meta.data_type
            column_type = COLUMN_TYPE_MAP.get(data_type, None)
            column_name = pg_row_meta.column_name

            if column_type:
                kwargs: t.Dict[str, t.Any] = {
                    "null": pg_row_meta.is_nullable == "YES",
                    "unique": constraints.is_unique(column_name=column_name),
                }

                if constraints.is_primary_key(column_name=column_name):
                    kwargs["primary_key"] = True
                    if column_type == Integer:
                        column_type = Serial

                if constraints.is_foreign_key(column_name=column_name):
                    fk_constraint_name = (
                        constraints.get_foreign_key_constraint_name(
                            column_name=column_name
                        )
                    )
                    column_type = ForeignKey
                    referenced_tablename = await get_foreign_key_reference(
                        table_class=Schema, constraint_name=fk_constraint_name
                    )
                    if referenced_tablename:
                        kwargs["references"] = create_table_class(
                            _snake_to_camel(referenced_tablename)
                        )
                    else:
                        kwargs["references"] = ForeignKeyPlaceholder
                    imports.add(
                        "from piccolo.columns.base import OnDelete, OnUpdate"
                    )

                imports.add(
                    "from piccolo.column_types import " + column_type.__name__
                )

                if column_type is Varchar:
                    kwargs["length"] = pg_row_meta.character_maximum_length

                columns[column_name] = column_type(**kwargs)
            else:
                warnings.append(f"{tablename}.{column_name} ['{data_type}']")

        table = create_table_class(
            class_name=_snake_to_camel(tablename),
            class_kwargs={"tablename": tablename},
            class_members=columns,
        )
        tables.append(table)

    return OutputSchema(
        imports=sorted(list(imports)), warnings=warnings, tables=tables
    )


# This is currently a beta version, and can be improved. However, having
# something working is still useful for people migrating large schemas to
# Piccolo.
async def generate(schema_name: str = "public"):
    """
    Automatically generates Piccolo Table classes by introspecting the
    database. Please check the generated code in case there are errors.

    """
    output_schema = await get_output_schema(schema_name=schema_name)

    output = output_schema.imports + [
        i._table_str(excluded_params=["index_method", "index", "choices"])
        for i in output_schema.tables
    ]

    if output_schema.warnings:
        warning_str = "\n".join(output_schema.warnings)

        output.append('"""')
        output.append(
            "WARNING: Unrecognised column types, added `Column` as a "
            "placeholder:"
        )
        output.append(warning_str)
        output.append('"""')

    nicely_formatted = black.format_str(
        "\n".join(output), mode=black.FileMode(line_length=79)
    )
    print(nicely_formatted)
