from __future__ import annotations
import asyncio
from concurrent.futures import ThreadPoolExecutor
import contextvars
from dataclasses import dataclass
import typing as t
import warnings

import asyncpg
from asyncpg.connection import Connection
from asyncpg.cursor import Cursor
from asyncpg.pool import Pool

from piccolo.engine.base import Batch, Engine
from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import Query
from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import colored_warning


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

    async def __aexit__(self, exception_type, exception, traceback):
        if exception:
            await self._transaction.rollback()
        else:
            await self._transaction.commit()

        await self.connection.close()

        return exception is not None


###############################################################################


class Atomic:
    """
    This is useful if you want to build up a transaction programatically, by
    adding queries to it.

    Usage:

    transaction = engine.atomic()
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

    async def _run_in_new_connection(self):
        connection = await asyncpg.connect(**self.engine.config)
        await self._run_queries(connection)

    async def run(self, in_pool=True):
        if in_pool and self.engine.pool:
            await self._run_in_pool()
        else:
            await self._run_in_new_connection()

    def run_sync(self):
        return run_sync(self._run_in_new_connection())


###############################################################################


class Transaction:
    """
    Used for wrapping queries in a transaction, using a context manager.
    Currently it's async only.

    Usage:

    async with engine.transaction():
        # Run some queries:
        await Band.select().run()

    """

    __slots__ = ("engine", "transaction", "context", "connection")

    def __init__(self, engine: PostgresEngine):
        self.engine = engine
        if self.engine.transaction_connection.get():
            raise TransactionError(
                "A transaction is already active - nested transactions aren't "
                "currently supported."
            )

    async def __aenter__(self):
        if self.engine.pool:
            self.connection = await self.engine.pool.acquire()
        else:
            self.connection = await self.engine.get_new_connection()

        self.transaction = self.connection.transaction()
        await self.transaction.start()
        self.context = self.engine.transaction_connection.set(self.connection)

    async def commit(self):
        await self.transaction.commit()

    async def rollback(self):
        await self.transaction.rollback()

    async def __aexit__(self, exception_type, exception, traceback):
        if exception:
            await self.rollback()
        else:
            await self.commit()

        if self.engine.pool:
            await self.engine.pool.release(self.connection)
        else:
            await self.connection.close()

        self.engine.transaction_connection.reset(self.context)

        return exception is None


###############################################################################


class PostgresEngine(Engine):

    __slots__ = ("config", "pool")

    engine_type = "postgres"
    min_version_number = 9.6

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config
        self.pool: t.Optional[Pool] = None
        database_name = config.get("database", "Unknown")
        self.transaction_connection = contextvars.ContextVar(
            f"pg_transaction_connection_{database_name}", default=None
        )
        super().__init__()

    def get_version(self) -> float:
        """
        Returns the version of Postgres being run.
        """
        loop = asyncio.new_event_loop()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                loop.run_until_complete,
                self._run_in_new_connection("SHOW server_version"),
            )

        try:
            response: t.Sequence[t.Dict] = future.result()
        except ConnectionRefusedError as exception:
            # Suppressing the exception, otherwise importing piccolo_conf.py
            # containing an engine will raise an ImportError.
            colored_warning("Unable to connect to database")
            print(exception)
            return 0.0
        else:
            server_version = response[0]["server_version"]
            major, minor = server_version.split(".")[:2]
            version = float(f"{major}.{minor}")
            return version

    ###########################################################################

    async def start_connnection_pool(self, **kwargs) -> None:
        if self.pool:
            warnings.warn(
                "A pool already exists - close it first if you want to create "
                "a new pool."
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

    async def get_new_connection(self) -> Connection:
        """
        Returns a new connection - doesn't retrieve it from the pool.
        """
        return await asyncpg.connect(**self.config)

    ###########################################################################

    async def batch(self, query: Query, batch_size: int = 100) -> AsyncBatch:
        connection = await self.get_new_connection()
        return AsyncBatch(
            connection=connection, query=query, batch_size=batch_size
        )

    ###########################################################################

    async def _run_in_pool(self, query: str, args: t.Sequence[t.Any] = []):
        if not self.pool:
            raise ValueError("A pool isn't currently running.")

        async with self.pool.acquire() as connection:
            response = await connection.fetch(query, *args)

        return response

    async def _run_in_new_connection(
        self, query: str, args: t.Sequence[t.Any] = []
    ):
        connection = await self.get_new_connection()
        results = await connection.fetch(query, *args)
        await connection.close()
        return results

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = True
    ):
        query, query_args = querystring.compile_string(
            engine_type=self.engine_type
        )

        # If running inside a transaction:
        connection = self.transaction_connection.get()
        if connection:
            return await connection.fetch(query, *query_args)
        elif in_pool and self.pool:
            return await self._run_in_pool(query, query_args)
        else:
            return await self._run_in_new_connection(query, query_args)

    def atomic(self) -> Atomic:
        return Atomic(engine=self)

    def transaction(self) -> Transaction:
        return Transaction(engine=self)
