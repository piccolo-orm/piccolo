from __future__ import annotations

import contextvars
import typing as t
from dataclasses import dataclass

from piccolo.engine.base import Batch, Engine, validate_savepoint_name
from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import DDL, Query
from piccolo.querystring import QueryString
from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import Level, colored_warning

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")

if t.TYPE_CHECKING:  # pragma: no cover
    from asyncpg.connection import Connection
    from asyncpg.cursor import Cursor
    from asyncpg.pool import Pool


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

    Usage::

        transaction = engine.atomic()
        transaction.add(Foo.create_table())

        # Either:
        transaction.run_sync()
        await transaction.run()

    """

    __slots__ = ("engine", "queries")

    def __init__(self, engine: PostgresEngine):
        self.engine = engine
        self.queries: t.List[t.Union[Query, DDL]] = []

    def add(self, *query: t.Union[Query, DDL]):
        self.queries += list(query)

    async def run(self):
        from piccolo.query.methods.objects import Create, GetOrCreate

        try:
            async with self.engine.transaction():
                for query in self.queries:
                    if isinstance(query, (Query, DDL, Create, GetOrCreate)):
                        await query.run()
                    else:
                        raise ValueError("Unrecognised query")
            self.queries = []
        except Exception as exception:
            self.queries = []
            raise exception from exception

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


###############################################################################


class Savepoint:
    def __init__(self, name: str, transaction: PostgresTransaction):
        self.name = name
        self.transaction = transaction

    async def rollback_to(self):
        validate_savepoint_name(self.name)
        await self.transaction.connection.execute(
            f"ROLLBACK TO SAVEPOINT {self.name}"
        )

    async def release(self):
        validate_savepoint_name(self.name)
        await self.transaction.connection.execute(
            f"RELEASE SAVEPOINT {self.name}"
        )


class PostgresTransaction:
    """
    Used for wrapping queries in a transaction, using a context manager.
    Currently it's async only.

    Usage::

        async with engine.transaction():
            # Run some queries:
            await Band.select().run()

    """

    __slots__ = (
        "engine",
        "transaction",
        "context",
        "connection",
        "_savepoint_id",
        "_parent",
        "_committed",
        "_rolled_back",
    )

    def __init__(self, engine: PostgresEngine, allow_nested: bool = True):
        """
        :param allow_nested:
            If ``True`` then if we try creating a new transaction when another
            is already active, we treat this as a no-op::

                async with DB.transaction():
                    async with DB.transaction():
                        pass

            If we want to disallow this behaviour, then setting
            ``allow_nested=False`` will cause a ``TransactionError`` to be
            raised.

        """
        self.engine = engine
        current_transaction = self.engine.current_transaction.get()

        self._savepoint_id = 0
        self._parent = None
        self._committed = False
        self._rolled_back = False

        if current_transaction:
            if allow_nested:
                self._parent = current_transaction
            else:
                raise TransactionError(
                    "A transaction is already active - nested transactions "
                    "aren't allowed."
                )

    async def __aenter__(self) -> PostgresTransaction:
        if self._parent is not None:
            return self._parent

        self.connection = await self.get_connection()
        self.transaction = self.connection.transaction()
        await self.begin()
        self.context = self.engine.current_transaction.set(self)
        return self

    async def get_connection(self):
        if self.engine.pool:
            return await self.engine.pool.acquire()
        else:
            return await self.engine.get_new_connection()

    async def begin(self):
        await self.transaction.start()

    async def commit(self):
        await self.transaction.commit()
        self._committed = True

    async def rollback(self):
        await self.transaction.rollback()
        self._rolled_back = True

    async def rollback_to(self, savepoint_name: str):
        """
        Used to rollback to a savepoint just using the name.
        """
        await Savepoint(name=savepoint_name, transaction=self).rollback_to()

    ###########################################################################

    def get_savepoint_id(self) -> int:
        self._savepoint_id += 1
        return self._savepoint_id

    async def savepoint(self, name: t.Optional[str] = None) -> Savepoint:
        name = name or f"savepoint_{self.get_savepoint_id()}"
        validate_savepoint_name(name)
        await self.connection.execute(f"SAVEPOINT {name}")
        return Savepoint(name=name, transaction=self)

    ###########################################################################

    async def __aexit__(self, exception_type, exception, traceback):
        if self._parent:
            return exception is None

        if exception:
            # The user may have manually rolled it back.
            if not self._rolled_back:
                await self.rollback()
        else:
            # The user may have manually committed it.
            if not self._committed and not self._rolled_back:
                await self.commit()

        if self.engine.pool:
            await self.engine.pool.release(self.connection)
        else:
            await self.connection.close()

        self.engine.current_transaction.reset(self.context)

        return exception is None


###############################################################################


class PostgresEngine(Engine[t.Optional[PostgresTransaction]]):
    """
    Used to connect to PostgreSQL.

    :param config:
        The config dictionary is passed to the underlying database adapter,
        asyncpg. Common arguments you're likely to need are:

        * host
        * port
        * user
        * password
        * database

        For example, ``{'host': 'localhost', 'port': 5432}``.

        See the `asyncpg docs <https://magicstack.github.io/asyncpg/current/api/index.html#connection>`_
        for all available options.

    :param extensions:
        When the engine starts, it will try and create these extensions
        in Postgres. If you're using a read only database, set this value to an
        empty tuple ``()``.

    :param log_queries:
        If ``True``, all SQL and DDL statements are printed out before being
        run. Useful for debugging.

    :param log_responses:
        If ``True``, the raw response from each query is printed out. Useful
        for debugging.

    :param extra_nodes:
        If you have additional database nodes (e.g. read replicas) for the
        server, you can specify them here. It's a mapping of a memorable name
        to a ``PostgresEngine`` instance. For example::

            DB = PostgresEngine(
                config={'database': 'main_db'},
                extra_nodes={
                    'read_replica_1': PostgresEngine(
                        config={
                            'database': 'main_db',
                            host: 'read_replicate.my_db.com'
                        },
                        extensions=()
                    )
                }
            )

        Note how we set ``extensions=()``, because it's a read only database.

        When executing a query, you can specify one of these nodes instead
        of the main database. For example::

            >>> await MyTable.select().run(node="read_replica_1")

    """  # noqa: E501

    __slots__ = (
        "config",
        "extensions",
        "log_queries",
        "log_responses",
        "extra_nodes",
        "pool",
        "current_transaction",
    )

    engine_type = "postgres"
    min_version_number = 10

    def __init__(
        self,
        config: t.Dict[str, t.Any],
        extensions: t.Sequence[str] = ("uuid-ossp",),
        log_queries: bool = False,
        log_responses: bool = False,
        extra_nodes: t.Optional[t.Mapping[str, PostgresEngine]] = None,
    ) -> None:
        if extra_nodes is None:
            extra_nodes = {}

        self.config = config
        self.extensions = extensions
        self.log_queries = log_queries
        self.log_responses = log_responses
        self.extra_nodes = extra_nodes
        self.pool: t.Optional[Pool] = None
        database_name = config.get("database", "Unknown")
        self.current_transaction = contextvars.ContextVar(
            f"pg_current_transaction_{database_name}", default=None
        )
        super().__init__()

    @staticmethod
    def _parse_raw_version_string(version_string: str) -> float:
        """
        The format of the version string isn't always consistent. Sometimes
        it's just the version number e.g. '9.6.18', and sometimes
        it contains specific build information e.g.
        '12.4 (Ubuntu 12.4-0ubuntu0.20.04.1)'. Just extract the major and
        minor version numbers.
        """
        version_segment = version_string.split(" ")[0]
        major, minor = version_segment.split(".")[:2]
        return float(f"{major}.{minor}")

    async def get_version(self) -> float:
        """
        Returns the version of Postgres being run.
        """
        try:
            response: t.Sequence[t.Dict] = await self._run_in_new_connection(
                "SHOW server_version"
            )
        except ConnectionRefusedError as exception:
            # Suppressing the exception, otherwise importing piccolo_conf.py
            # containing an engine will raise an ImportError.
            colored_warning(f"Unable to connect to database - {exception}")
            return 0.0
        else:
            version_string = response[0]["server_version"]
            return self._parse_raw_version_string(
                version_string=version_string
            )

    def get_version_sync(self) -> float:
        return run_sync(self.get_version())

    async def prep_database(self):
        for extension in self.extensions:
            try:
                await self._run_in_new_connection(
                    f'CREATE EXTENSION IF NOT EXISTS "{extension}"',
                )
            except asyncpg.exceptions.InsufficientPrivilegeError:
                colored_warning(
                    f"=> Unable to create {extension} extension - some "
                    "functionality may not behave as expected. Make sure "
                    "your database user has permission to create "
                    "extensions, or add it manually using "
                    f'`CREATE EXTENSION "{extension}";`',
                    level=Level.medium,
                )

    ###########################################################################
    # These typos existed in the codebase for a while, so leaving these proxy
    # methods for now to ensure backwards compatibility.

    async def start_connnection_pool(self, **kwargs) -> None:
        colored_warning(
            "`start_connnection_pool` is a typo - please change it to "
            "`start_connection_pool`.",
            category=DeprecationWarning,
        )
        return await self.start_connection_pool()

    async def close_connnection_pool(self, **kwargs) -> None:
        colored_warning(
            "`close_connnection_pool` is a typo - please change it to "
            "`close_connection_pool`.",
            category=DeprecationWarning,
        )
        return await self.close_connection_pool()

    ###########################################################################

    async def start_connection_pool(self, **kwargs) -> None:
        if self.pool:
            colored_warning(
                "A pool already exists - close it first if you want to create "
                "a new pool.",
            )
        else:
            config = dict(self.config)
            config.update(**kwargs)
            self.pool = await asyncpg.create_pool(**config)

    async def close_connection_pool(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
        else:
            colored_warning("No pool is running.")

    ###########################################################################

    async def get_new_connection(self) -> Connection:
        """
        Returns a new connection - doesn't retrieve it from the pool.
        """
        return await asyncpg.connect(**self.config)

    ###########################################################################

    async def batch(
        self,
        query: Query,
        batch_size: int = 100,
        node: t.Optional[str] = None,
    ) -> AsyncBatch:
        """
        :param query:
            The database query to run.
        :param batch_size:
            How many rows to fetch on each iteration.
        :param node:
            Which node to run the query on (see ``extra_nodes``). If not
            specified, it runs on the main Postgres node.
        """
        engine: t.Any = self.extra_nodes.get(node) if node else self
        connection = await engine.get_new_connection()
        return AsyncBatch(
            connection=connection, query=query, batch_size=batch_size
        )

    ###########################################################################

    async def _run_in_pool(
        self, query: str, args: t.Optional[t.Sequence[t.Any]] = None
    ):
        if args is None:
            args = []
        if not self.pool:
            raise ValueError("A pool isn't currently running.")

        async with self.pool.acquire() as connection:
            response = await connection.fetch(query, *args)

        return response

    async def _run_in_new_connection(
        self, query: str, args: t.Optional[t.Sequence[t.Any]] = None
    ):
        if args is None:
            args = []
        connection = await self.get_new_connection()

        try:
            results = await connection.fetch(query, *args)
        except asyncpg.exceptions.PostgresError as exception:
            await connection.close()
            raise exception

        await connection.close()
        return results

    async def run_querystring(
        self, querystring: QueryString, in_pool: bool = True
    ):
        query, query_args = querystring.compile_string(
            engine_type=self.engine_type
        )

        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=querystring.__str__())

        # If running inside a transaction:
        current_transaction = self.current_transaction.get()
        if current_transaction:
            response = await current_transaction.connection.fetch(
                query, *query_args
            )
        elif in_pool and self.pool:
            response = await self._run_in_pool(query, query_args)
        else:
            response = await self._run_in_new_connection(query, query_args)

        if self.log_responses:
            self.print_response(query_id=query_id, response=response)

        return response

    async def run_ddl(self, ddl: str, in_pool: bool = True):
        query_id = self.get_query_id()

        if self.log_queries:
            self.print_query(query_id=query_id, query=ddl)

        # If running inside a transaction:
        current_transaction = self.current_transaction.get()
        if current_transaction:
            response = await current_transaction.connection.fetch(ddl)
        elif in_pool and self.pool:
            response = await self._run_in_pool(ddl)
        else:
            response = await self._run_in_new_connection(ddl)

        if self.log_responses:
            self.print_response(query_id=query_id, response=response)

        return response

    def atomic(self) -> Atomic:
        return Atomic(engine=self)

    def transaction(self, allow_nested: bool = True) -> PostgresTransaction:
        return PostgresTransaction(engine=self, allow_nested=allow_nested)
