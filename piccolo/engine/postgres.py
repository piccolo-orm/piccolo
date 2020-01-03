from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import typing as t
import warnings

import asyncpg
from asyncpg.connection import Connection
from asyncpg.cursor import Cursor
from asyncpg.pool import Pool

from piccolo.engine.base import Batch, Engine
from piccolo.query.base import Query
from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync


@dataclass
class AsyncBatch(Batch):

    connection: Connection
    query: Query
    batch_size: int

    # Set internally
    _transaction = None
    _cursor: t.Optional[Cursor] = None

    @property
    def cursor(self) -> Cursor:
        if not self._cursor:
            raise ValueError("_cursor not set")
        return self._cursor

    async def next(self) -> t.List[t.Dict]:
        data = await self.cursor.fetch(self.batch_size)
        return await self.query._process_results(data)

    def __aiter__(self):
        return self

    async def __anext__(self):
        response = await self.next()
        if response == []:
            raise StopAsyncIteration()
        return response

    async def __aenter__(self):
        self._transaction = self.connection.transaction()
        await self._transaction.start()
        querystring = self.query.querystrings[0]
        template, template_args = querystring.compile_string()

        self._cursor = await self.connection.cursor(template, *template_args)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        print("waiting to exit")
        await self._transaction.commit()
        await self.connection.close()


###############################################################################


class Transaction:
    """
    Usage:

    transaction = engine.transaction()
    transaction.add(Foo.create_table())

    # Either:
    transaction.run_sync()
    await transaction.run()
    """

    __slots__ = ("engine", "queries")

    def __init__(self, engine: PostgresEngine):
        self.engine = engine
        self.queries: t.List[Query] = []

    def add(self, *query: Query):
        self.queries += list(query)

    async def _run_queries(self, connection):
        async with connection.transaction():
            for query in self.queries:
                for querystring in query.querystrings:
                    _query, args = querystring.compile_string(
                        engine_type=self.engine.engine_type
                    )
                    await connection.execute(_query, *args)

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

    async def run(self, in_pool=True):
        if in_pool and self.engine.pool:
            await self._run_in_pool()
        else:
            await self._run()

    def run_sync(self):
        return run_sync(self._run())


###############################################################################
class PostgresEngine(Engine):

    __slots__ = ("config", "pool")

    engine_type = "postgres"
    min_version_number = 9.6

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config
        self.pool: t.Optional[Pool] = None
        super().__init__()

    def get_version(self) -> float:
        """
        Returns the version of Postgres being run.
        """
        loop = asyncio.new_event_loop()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                loop.run_until_complete, self.run("SHOW server_version")
            )

        response: t.Array[t.Dict] = future.result()

        server_version = response[0]["server_version"]
        major, minor, _ = server_version.split(".")
        version = float(f"{major}.{minor}")
        return version

    ###########################################################################

    async def start_connnection_pool(self, **kwargs) -> None:
        if self.pool:
            warnings.warn(
                "A pool already exists - close it first if you want to create a new pool."
            )
        else:
            config = dict(self.config)
            config.update(**kwargs)
            self.pool = await asyncpg.create_pool(**config)

    async def close_connnection_pool(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
        else:
            warnings.warn("No pool is running.")

    ###########################################################################

    async def get_connection(self) -> Connection:
        return await asyncpg.connect(**self.config)

    ###########################################################################

    async def batch(self, query: Query, batch_size=100) -> AsyncBatch:
        connection = await self.get_connection()
        return AsyncBatch(
            connection=connection, query=query, batch_size=batch_size
        )

    ###########################################################################

    async def run_in_pool(self, query: str, args: t.List[t.Any] = []):
        if not self.pool:
            raise ValueError("A pool isn't currently running.")

        async with self.pool.acquire() as connection:
            response = await connection.fetch(query, *args)

        return response

    async def run(self, query: str, args: t.List[t.Any] = []):
        connection = await self.get_connection()
        results = await connection.fetch(query, *args)
        await connection.close()
        return results

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = True
    ):
        query, args = querystring.compile_string(engine_type=self.engine_type)
        if in_pool and self.pool:
            return await self.run_in_pool(query, args)
        else:
            return await self.run(query, args)

    def transaction(self) -> Transaction:
        return Transaction(engine=self)
