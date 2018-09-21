import typing as t

import asyncpg
from asyncpg.pool import Pool

from .base import Engine


class PostgresEngine(Engine):
    """
    Currently when using run ...  it sets up a connection each time.

    When instantiated ... create the connection pool ...

    Needs to be a singleton that's shared by all the tables.
    """

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config

    async def get_pool(self) -> Pool:
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                **self.config
            )
        return self.pool

    async def run(self, query: str):
        pool = await self.get_pool()

        connection = await pool.acquire()
        try:
            response = await connection.fetch(query)
        except Exception:
            pass
        finally:
            await pool.release(connection)

        return response
