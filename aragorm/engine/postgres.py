import typing as t

import asyncpg

from .base import Engine


class PostgresEngine(Engine):
    """
    Currently when using run ...  it sets up a connection each time.

    When instantiated ... create the connection pool ...

    Needs to be a singleton that's shared by all the tables.
    """

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config

    async def run(self, query: str):
        conn = await asyncpg.connect(**self.config)
        results = await conn.fetch(query)
        await conn.close()
        return results
