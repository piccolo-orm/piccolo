
import asyncio
import typing as t

import asyncpg
from asyncpg.pool import Pool

from .base import Engine
from ..query.base import Query
from ..utils.sync import run_sync


class Transaction():
    """
    Usage:

    transaction = engine.Transaction()
    transaction.add(Foo.create)
    transaction.run_sync()
    """

    def __init__(self, engine):
        self.engine = engine
        self.queries = []

    def add(self, *query: Query):
        self.queries += list(query)

    async def _run_queries(self, connection):
        async with connection.transaction():
            for query in self.queries:
                await connection.execute(query.__str__())

        self.queries = []

    async def _run_in_pool(self):
        pool = await self.engine.get_pool()
        connection = await pool.acquire()

        try:
            await self._run_queries(connection)
        except Exception:
            pass
        finally:
            await pool.release(connection)

    async def _run(self):
        connection = await asyncpg.connect(**self.engine.config)
        await self._run_queries(connection)

    async def run(self):
        await self._run_in_pool()

    def run_sync(self):
        return run_sync(
            self._run()
        )


class PostgresEngine(Engine):
    """
    Currently when using run ...  it sets up a connection each time.

    When instantiated ... create the connection pool ...

    Needs to be a singleton that's shared by all the tables.
    """

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config
        self.pool: t.Optional[Pool] = None
        self.loop: t.Optional[asyncio.AbstractEventLoop] = None

    async def get_pool(self) -> Pool:
        loop = asyncio.get_event_loop()
        if not self.pool or (self.loop != loop):
            self.pool = await asyncpg.create_pool(
                **self.config
            )
            self.loop = loop
        return self.pool

    async def run_in_pool(self, query: str):
        pool = await self.get_pool()

        connection = await pool.acquire()
        try:
            response = await connection.fetch(query)
        except Exception:
            pass
        finally:
            await pool.release(connection)

        return response

    async def run(self, query: str):
        connection = await asyncpg.connect(**self.config)
        results = await connection.fetch(query)
        await connection.close()
        return results

    def transaction(self):
        return Transaction(engine=self)
