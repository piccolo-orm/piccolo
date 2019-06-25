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

    async def run_in_pool(
        self,
        query: str,
        args: t.List[t.Any] = [],
        query_type: str = 'generic'
    ):
        raise NotImplementedError

    async def run(
        self,
        query: str,
        args: t.List[t.Any] = [],
        query_type: str = 'generic'
    ):
        async with aiosqlite.connect(self.path) as connection:
            connection.row_factory = dict_factory
            async with connection.execute(query, args) as cursor:
                cursor.row_factory = dict_factory
                await connection.commit()
                response = await cursor.fetchall()
                # print(query)
                # print(args)
                # print(response)

                # print(query_type)
                if query_type == 'insert':
                    return [{'id': cursor.lastrowid}]
                else:
                    return response

    async def run_querystring(
        self,
        querystring: QueryString,
        in_pool: bool = False
    ):
        if in_pool:
            return await self.run_in_pool(
                *querystring.compile_string(engine_type=self.engine_type),
                query_type=querystring.query_type
            )
        else:
            return await self.run(
                *querystring.compile_string(engine_type=self.engine_type),
                query_type=querystring.query_type
            )

    def transaction(self):
        raise NotImplementedError
