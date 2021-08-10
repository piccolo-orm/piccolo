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

    @classmethod
    def get_column_name_str(cls) -> str:
        return ", ".join([i.name for i in dataclasses.fields(cls)])


@dataclasses.dataclass
class TableConstraints:
    constraints: t.List[Constraint]

    def __post_init__(self):
        foreign_key_names: t.List[str] = []
        unique_key_names: t.List[str] = []
        primary_key_names: t.List[str] = []

        for constraint in self.constraints:
            if constraint.constraint_type == "FOREIGN KEY":
                foreign_key_names.append(constraint.constraint_name)
            elif constraint.constraint_type == "PRIMARY KEY":
                primary_key_names.append(constraint.constraint_name)
            elif constraint.constraint_name == "UNIQUE":
                primary_key_names.append(primary_key_names)

        self.foreign_key_names = foreign_key_names
        self.unique_key_names = unique_key_names
        self.primary_key_names = primary_key_names

    def is_primary_key(self, column_name: str, tablename: str) -> bool:
        for i in self.primary_key_names:
            if i == f"{tablename}_pkey":
                return True

        return False

    def is_unique(self, column_name: str, tablename: str) -> bool:
        for i in self.unique_key_names:
            if i.startswith(f"{tablename}_{column_name}"):
                return True

        return False

    def is_foreign_key(self, column_name: str, tablename: str) -> bool:
        for i in self.foreign_key_names:
            if i.startswith(f"{tablename}_{column_name}"):
                return True

        return False


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
    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.

    """
    constraints = await table_class.raw(
        (
            f"SELECT {Constraint.get_column_name_str()} FROM "
            "information_schema.table_constraints "
            "WHERE table_schema = {} "
            "AND table_name = {} "
        ),
        schema_name,
        tablename,
    )
    return TableConstraints(constraints=[Constraint(**i) for i in constraints])


async def get_tablenames(
    table_class: t.Type[Table], schema_name: str = "public"
) -> t.List[str]:
    """
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
    :returns:
        A list, with each item containing information about a column in the
        table.

    """
    row_meta_list = await table_class.raw(
        (
            f"SELECT {RowMeta.get_column_name_str()} FROM "
            "information_schema.columns "
            "WHERE table_schema = {} "
            "AND TABLE_NAME = {}"
        ),
        schema_name,
        tablename,
    ).run()
    return [RowMeta(**row_meta) for row_meta in row_meta_list]


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
                    "unique": constraints.is_unique(
                        column_name=column_name, tablename=tablename
                    ),
                }

                if constraints.is_primary_key(
                    column_name=column_name, tablename=tablename
                ):
                    kwargs["primary_key"] = True
                    if column_type == Integer:
                        column_type = Serial

                if constraints.is_foreign_key(
                    column_name=column_name, tablename=tablename
                ):
                    column_type = ForeignKey
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
