from __future__ import annotations

import contextvars
import typing as t
from dataclasses import dataclass

from piccolo.engine.base import Batch, Engine
from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import DDL, Query
from piccolo.querystring import QueryString
from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import Level, colored_warning

from .postgres import PostgresEngine
from .postgres import Transaction as PostgresTransaction
from .postgres import Atomic as PostgresAtomic
from .postgres import AsyncBatch as PostgresAsyncBatch

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")

if t.TYPE_CHECKING:  # pragma: no cover
    from asyncpg.connection import Connection
    from asyncpg.cursor import Cursor
    from asyncpg.pool import Pool


@dataclass
class AsyncBatch(PostgresAsyncBatch):

    connection: Connection
    query: Query
    batch_size: int

    # Set internally
    _transaction = None
    _cursor: t.Optional[Cursor] = None


###############################################################################


class Atomic(PostgresAtomic):
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

    def __init__(self, engine: CockroachDBEngine):
        self.engine = engine
        self.queries: t.List[Query] = []
        super().__init__()


###############################################################################


class Transaction(PostgresTransaction):
    """
    Used for wrapping queries in a transaction, using a context manager.
    Currently it's async only.

    Usage::

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
        super().__init__()

###############################################################################


class CockroachDBEngine(PostgresEngine):
    """
    An extension of the Postgresql backend.
    """

    engine_type = "cockroachdb"
    #min_version_number = 9.6

    def __init__(
        self,
        config: t.Dict[str, t.Any],
        extensions: t.Sequence[str] = (),
        log_queries: bool = False,
        extra_nodes: t.Dict[str, CockroachDBEngine] = None,
    ) -> None:
        if extra_nodes is None:
            extra_nodes = {}

        self.config = config
        self.extensions = extensions
        self.log_queries = log_queries
        self.extra_nodes = extra_nodes
        self.pool: t.Optional[Pool] = None
        database_name = config.get("database", "Unknown")
        self.transaction_connection = contextvars.ContextVar(
            f"pg_transaction_connection_{database_name}", default=None
        )
        super().__init__()
