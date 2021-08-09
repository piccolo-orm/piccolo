import dataclasses
import typing as t

import black
from typing_extensions import Literal

from piccolo.columns.base import Column
from piccolo.columns.column_types import (
    UUID,
    BigInt,
    Boolean,
    Integer,
    Numeric,
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


@dataclasses.dataclass
class PostgresRowMeta:
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
class PostgresContraint:
    contraint_type: Literal["PRIMARY KEY", "UNIQUE", "FOREIGN KEY", "CHECK"]
    constraint_name: str

    @classmethod
    def get_column_name_str(cls) -> str:
        return ", ".join([i.name for i in dataclasses.fields(cls)])


COLUMN_TYPE_MAP = {
    "bigint": BigInt,
    "boolean": Boolean,
    "character varying": Varchar,
    "integer": Integer,
    "numeric": Numeric,
    "smallint": SmallInt,
    "text": Text,
    "timestamp without time zone": Timestamp,
    "timestamp with time zone": Timestamptz,
    "uuid": UUID,
}


async def get_foreign_keys(
    table_class: t.Type[Table], schema_name: str = "public"
):
    """
    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.

    """
    foreign_key_meta: t.List[str] = await table_class.raw(
        (
            f"SELECT {PostgresContraint.get_column_name_str()} FROM "
            "information_schema.table_constraints "
            "WHERE table_schema = {} "
            "AND table_name = {};"
        ),
        schema_name,
    )
    return foreign_key_meta


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
                "schemaname = {};"
            ),
            schema_name,
        ).run()
    ]
    return tablenames


async def get_table_schema(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> t.List[PostgresRowMeta]:
    """
    :returns:
        A list, with each item containing information about a colum in the
        table.

    """
    row_meta_list = await table_class.raw(
        (
            f"SELECT {PostgresRowMeta.get_column_name_str()} FROM "
            "information_schema.columns "
            "WHERE table_schema = {} "
            "AND TABLE_NAME = {};"
        ),
        schema_name,
        tablename,
    ).run()
    return [PostgresRowMeta(**row_meta) for row_meta in row_meta_list]


# This is currently a beta version, and can be improved. However, having
# something working is still useful for people migrating large schemas to
# Piccolo.
async def generate(schema_name: str = "public"):
    """
    Automatically generates Piccolo Table classes by introspecting the
    database. Please check the generated code in case there are errors.

    """
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
        pass

    tablenames = await get_tablenames(Schema, schema_name=schema_name)

    output: t.List[str] = []
    imports: t.Set[str] = {"from piccolo.table import Table"}
    warnings: t.List[str] = []

    for tablename in tablenames:
        table_schema = await get_table_schema(Schema, tablename, schema_name)

        columns: t.Dict[str, Column] = {}

        for pg_row_meta in table_schema:
            data_type = pg_row_meta.data_type
            column_type = COLUMN_TYPE_MAP.get(data_type, None)
            column_name = pg_row_meta.column_name

            if column_type:
                kwargs: t.Dict[str, t.Any] = {
                    "null": pg_row_meta.is_nullable == "YES"
                }

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
        output.append(table._table_str())

    output = sorted(list(imports)) + output

    if warnings:
        warning_str = "\n".join(warnings)

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
