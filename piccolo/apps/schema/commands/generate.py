from __future__ import annotations

import dataclasses
import typing as t

import black
from typing_extensions import Literal

from piccolo.apps.migrations.auto.serialisation import serialise_params
from piccolo.columns.base import Column
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    BigInt,
    Boolean,
    Bytea,
    Date,
    DoublePrecision,
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
from piccolo.table import Table, create_table_class, sort_table_classes
from piccolo.utils.naming import _snake_to_camel

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.engine.base import Engine


class ForeignKeyPlaceholder(Table):
    pass


@dataclasses.dataclass
class ConstraintTable:
    name: str = ""
    schema: str = ""


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
    constraint_schema: t.Optional[str] = None
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

    def get_foreign_key_constraint_name(self, column_name) -> ConstraintTable:
        for i in self.foreign_key_constraints:
            if i.column_name == column_name:
                return ConstraintTable(i.constraint_name, i.constraint_schema)

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

    imports: t.List[str] = dataclasses.field(default_factory=list)
    warnings: t.List[str] = dataclasses.field(default_factory=list)
    tables: t.List[t.Type[Table]] = dataclasses.field(default_factory=list)

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
    "double precision": DoublePrecision,
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
    :param tablename:
    Name of the table.
    :param schema_name:
    Name of the schema.


    """
    constraints = await table_class.raw(
        (
            "SELECT tc.constraint_name, tc.constraint_type, kcu.column_name, tc.constraint_schema "  # noqa: E501
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

    :param schema_name:
        name of the schema
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
    table_class: t.Type[Table], constraint_name: str, constraint_schema: str
) -> ConstraintTable:  # type: ignore
    """
    Retrieve the name of the table that a foreign key is referencing.
    """
    response = await table_class.raw(
        (
            "SELECT table_name, table_schema "
            "FROM information_schema.constraint_column_usage "
            "WHERE constraint_name = {} AND constraint_schema  = {};"
        ),
        constraint_name,
        constraint_schema,
    )
    if len(response) > 0:
        return ConstraintTable(
            response[0]["table_name"], response[0]["table_schema"]
        )
    else:
        return ConstraintTable()


def get_table_name(name: str, schema: str) -> str:
    if schema == "public":
        return name
    return f"{schema}.{name}"


async def create_table(
    Schema: t.Type[Table],
    tablename: str,
    schema_name: str,
    output_schema: OutputSchema,
) -> t.Type[Table]:
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
        if not column_type:
            output_schema.warnings.append(
                f"{tablename}.{column_name} ['{data_type}']"
            )
            column_type = Column

        kwargs: t.Dict[str, t.Any] = {
            "null": pg_row_meta.is_nullable == "YES",
            "unique": constraints.is_unique(column_name=column_name),
        }

        if constraints.is_primary_key(column_name=column_name):
            kwargs["primary_key"] = True
            if column_type == Integer:
                column_type = Serial

        if constraints.is_foreign_key(column_name=column_name):
            fk_constraint_table = constraints.get_foreign_key_constraint_name(
                column_name=column_name
            )
            column_type = ForeignKey
            constraint_table = await get_foreign_key_reference(
                table_class=Schema,
                constraint_name=fk_constraint_table.name,
                constraint_schema=fk_constraint_table.schema,
            )
            if constraint_table.name:
                kwargs["references"] = await create_table(
                    Schema,
                    constraint_table.name,
                    constraint_table.schema,
                    output_schema,
                )
            else:
                kwargs["references"] = ForeignKeyPlaceholder

        output_schema.imports.append(
            "from piccolo.columns.column_types import " + column_type.__name__
        )

        if column_type is Varchar:
            kwargs["length"] = pg_row_meta.character_maximum_length

        column = column_type(**kwargs)

        serialised_params = serialise_params(column._meta.params)
        for extra_import in serialised_params.extra_imports:
            output_schema.imports.append(extra_import.__repr__())

        columns[column_name] = column

    table = create_table_class(
        class_name=_snake_to_camel(tablename),
        class_kwargs={"tablename": get_table_name(tablename, schema_name)},
        class_members=columns,
    )
    output_schema.tables.append(table)
    return table


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

    output_schema = OutputSchema()

    for tablename in tablenames:
        await create_table(Schema, tablename, schema_name, output_schema)

    # Sort the tables based on their ForeignKeys.
    output_schema.tables = sort_table_classes(output_schema.tables)
    output_schema.imports = sorted(list(set(output_schema.imports)))

    # We currently don't show the index argument for columns in the output,
    # so we don't need this import for now:
    output_schema.imports.remove(
        "from piccolo.columns.indexes import IndexMethod"
    )

    return output_schema


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
