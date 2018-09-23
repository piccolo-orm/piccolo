import asyncio
import typing as t

import asyncpg

from .base import Engine
from ..query.base import Query


class Transaction():
    """
    Usage:

    transaction = engine.Transaction()
    transaction.add(Foo.create())
    transaction.run_sync()
    """

    def __init__(self, engine):
        self.engine = engine
        self.queries = []

    def add(self, *query: Query):
        self.queries += list(query)

    async def run(self):
        connection = await asyncpg.connect(**self.engine.config)
        async with connection.transaction():
            for query in self.queries:
                await connection.execute(query.__str__())

        # In case the transaction object gets reused:
        self.queries = []

    def run_sync(self):
        return asyncio.run(self.run())


class PostgresEngine(Engine):
    """
    Currently when using run ...  it sets up a connection each time.

    When instantiated ... create the connection pool ...

    Needs to be a singleton that's shared by all the tables.
    """

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config

    async def run(self, query: str):
        connection = await asyncpg.connect(**self.config)
        results = await connection.fetch(query)
        await connection.close()
        return results

    def transaction(self):
        return Transaction(engine=self)
