import sqlite3
import typing as t

import aiosqlite

from piccolo.engine.base import Engine
from piccolo.querystring import QueryString
from piccolo.utils.warnings import colored_warning


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLiteEngine(Engine):

    engine_type = "sqlite"
    min_version_number = 3.25

    def __init__(self, path: str = "piccolo.sqlite") -> None:
        self.path = path
        super().__init__()

    def get_version(self) -> float:
        """
        Warn if the version of SQLite isn't supported.
        """
        major, minor, _ = sqlite3.sqlite_version.split(".")
        return float(f"{major}.{minor}")

    async def run_in_pool(
        self, query: str, args: t.List[t.Any] = [], query_type: str = "generic"
    ):
        raise NotImplementedError

    async def run(
        self, query: str, args: t.List[t.Any] = [], query_type: str = "generic"
    ):
        async with aiosqlite.connect(
            self.path, detect_types=sqlite3.PARSE_DECLTYPES
        ) as connection:
            connection.row_factory = dict_factory
            async with connection.execute(query, args) as cursor:
                cursor.row_factory = dict_factory
                await connection.commit()
                response = await cursor.fetchall()
                # print(query)
                # print(args)
                # print(response)

                # print(query_type)
                if query_type == "insert":
                    return [{"id": cursor.lastrowid}]
                else:
                    return response

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = False
    ):
        return await self.run(
            *querystring.compile_string(engine_type=self.engine_type),
            query_type=querystring.query_type,
        )

    def transaction(self):
        raise NotImplementedError
