import asyncio
import typing as t

import asyncpg

from .base import Engine


class Transaction():
    """
    Usage:

    with await Transaction() as transaction:
        transaction.add(Foo.create())
    """

    def __init__(self, engine):
        self.engine = engine
        self.queries = []

    def add(self, *query: str):
        self.queries += list(query)

    async def run(self):
        connection = await asyncpg.connect(**self.engine.config)
        async with connection.transaction():
            for query in self.queries:
                await connection.execute(query)

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
