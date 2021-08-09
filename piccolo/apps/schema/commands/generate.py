import dataclasses
import typing as t

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
                    "uuid": UUID,
                }

                data_type = pg_row_meta.data_type
                column_type = column_type_map.get(data_type, None)
                column_name = pg_row_meta.column_name
                if not column_type:
                    warnings.append(
                        f"{tablename}.{column_name} ['{data_type}']"
                    )

                if column_type is Integer:
                    columns[pg_row_meta.column_name] = Integer()

            table = create_table_class(
                class_name=class_name,
                class_kwargs={"tablename": tablename},
                class_members=columns,
            )
            print(table)

    if warnings:
        print('"""')
        print("WARNINGS")
        print("Unrecognised column types, added `Column` as a placeholder:\n")
        print("\n".join(warnings))
        print('"""')
