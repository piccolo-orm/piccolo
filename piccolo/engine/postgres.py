from __future__ import annotations
import typing as t
import warnings

import asyncpg
from asyncpg.pool import Pool
from asgiref.sync import async_to_sync

from piccolo.engine.base import Engine
from piccolo.query.base import Query
from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import colored_warning


class Transaction:
    """
    Usage:

    transaction = engine.Transaction()
    transaction.add(Foo.create())
    transaction.run_sync()
    """

    def __init__(self, engine: PostgresEngine):
        self.engine = engine
        self.queries: t.List[Query] = []

    def add(self, *query: Query):
        self.queries += list(query)

    async def _run_queries(self, connection):
        async with connection.transaction():
            for query in self.queries:
                _query, args = query.querystring.compile_string(
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


class PostgresEngine(Engine):

    engine_type = "postgres"
    min_version_number = 9.6

    def __init__(self, config: t.Dict[str, t.Any]) -> None:
        self.config = config
        self.pool: t.Optional[Pool] = None
        super().__init__()

    def get_version(self) -> float:
        response = async_to_sync(self.run)("SHOW server_version")
        server_version = response[0]["server_version"]
        major, minor, _ = server_version.split(".")
        version = float(f"{major}.{minor}")
        return version

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

    async def run_in_pool(self, query: str, args: t.List[t.Any] = []):
        if not self.pool:
            raise ValueError("A pool isn't currently running.")

        async with self.pool.acquire() as connection:
            response = await connection.fetch(query, *args)

        return response

    async def run(self, query: str, args: t.List[t.Any] = []):
        connection = await asyncpg.connect(**self.config)
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
