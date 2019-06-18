import sqlite3
import typing as t

import aiosqlite

from piccolo.engine.base import Engine
from piccolo.querystring import QueryString


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLiteEngine(Engine):

    engine_type = 'sqlite'

    def __init__(self, path: str = 'piccolo.sqlite') -> None:
        self.path = path

    async def run_in_pool(self, query: str, args: t.List[t.Any] = []):
        raise NotImplementedError

    async def run(self, query: str, args: t.List[t.Any] = []):
        async with aiosqlite.connect(self.path) as connection:
            connection.row_factory = dict_factory
            async with connection.execute(query, args) as cursor:
                cursor.row_factory = dict_factory
                await connection.commit()
                response = await cursor.fetchall()
                print(cursor.lastrowid)
                print(query)
                print(args)
                print(response)
                return response

    async def _run(self, query: str, args: t.List[t.Any] = []):
        connection = sqlite3.connect(self.path)
        connection.row_factory = dict_factory
        cursor = connection.execute(query, args)
        cursor.row_factory = dict_factory
        connection.commit()
        response = cursor.fetchall()
        cursor.close()
        connection.close()
        print(cursor.lastrowid)
        print(query)
        print(args)
        print(response)
        import ipdb; ipdb.set_trace()
        return response

    async def run_querystring(
        self,
        querystring: QueryString,
        in_pool: bool = False
    ):
        if in_pool:
            return await self.run_in_pool(
                *querystring.compile_string(engine_type=self.engine_type)
            )
        else:
            return await self.run(
                *querystring.compile_string(engine_type=self.engine_type)
            )

    def transaction(self):
        raise NotImplementedError
