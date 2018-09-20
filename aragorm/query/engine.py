import asyncio
import typing as t

import asyncpg
from asyncpg.pool import Pool


class Engine():
    """
    Currently when using run ...  it sets up a connection each time.

    When instantiated ... create the connection pool ...

    Needs to be a singleton that's shared by all the tables.
    """

    pool: t.Optional[Pool] = None

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config

    async def get_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                **self.config
            )
        return self.pool

    async def run(self, query: str):
        pool = await self.get_pool()

        async with pool.acquire() as connection:
            response = connection.fetch(query)

        return response

    def run_sync(self, query: str):
        return asyncio.run(
            self.run(query)
        )
