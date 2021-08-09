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

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.engine.base import Engine


@dataclasses.dataclass
class PostgresRowMeta:
    column_default: str
    column_name: str
    is_nullable: Literal["YES", "NO"]
    ordinal_position: int
    table_name: str
    character_maximum_length: t.Optional[int]
    data_type: str


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

    tablenames: t.List[str] = [
        i["tablename"]
        for i in await Schema.raw(
            (
                "SELECT tablename FROM pg_catalog.pg_tables WHERE "
                "schemaname = {};"
            ),
            schema_name,
        ).run()
    ]

    schema_column_names = ", ".join(
        [i.name for i in dataclasses.fields(PostgresRowMeta)]
    )

    output = []
    warnings: t.List[str] = []

    for tablename in tablenames:
        row_meta_list = await Schema.raw(
            (
                f"SELECT {schema_column_names} FROM "
                "information_schema.columns "
                "WHERE table_schema = {} "
                "AND TABLE_NAME = {};"
            ),
            schema_name,
            tablename,
        ).run()

        class_name = tablename.title()

        if row_meta_list:
            columns: t.Dict[str, Column] = {}

            for row_meta in row_meta_list:
                pg_row_meta = PostgresRowMeta(**row_meta)

                column_type_map = {
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

                data_type = pg_row_meta.data_type
                column_type = column_type_map.get(data_type, None)
                column_name = pg_row_meta.column_name

                if column_type:
                    null = pg_row_meta.is_nullable == "YES"
                    columns[pg_row_meta.column_name] = column_type(
                        null=null
                    )
                else:
                    warnings.append(
                        f"{tablename}.{column_name} ['{data_type}']"
                    )

            table = create_table_class(
                class_name=class_name,
                class_kwargs={"tablename": tablename},
                class_members=columns,
            )
            output.append(table._table_str())

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
