
import typing as t

import aiosqlite

from piccolo.engine.base import Engine
from piccolo.querystring import QueryString


class SQLiteEngine(Engine):

    def __init__(self, path: str = 'piccolo.sqlite') -> None:
        self.path = path

    async def run_in_pool(self, query: str, args: t.List[t.Any] = []):
        raise NotImplementedError

    async def run(self, query: str, args: t.List[t.Any] = []):
        async with aiosqlite.connect(self.path) as db:
            try:
                async with db.execute(query, args) as cursor:
                    return await cursor.fetchall()
            except Exception:
                print(query, args)

    async def run_querystring(
        self,
        querystring: QueryString,
        in_pool: bool = False
    ):
        if in_pool:
            return await self.run_in_pool(
                *querystring.compile_string(engine_type='sqlite')
            )
        else:
            return await self.run(
                *querystring.compile_string(engine_type='sqlite')
            )

    def transaction(self):
        raise NotImplementedError
