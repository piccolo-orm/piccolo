from __future__ import annotations

import contextvars
import typing as t

from piccolo.engine.exceptions import TransactionError
from piccolo.query.base import Query
from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.warnings import Level, colored_warning

from .postgres import Atomic as PostgresAtomic
from .postgres import PostgresEngine
from .postgres import Transaction as PostgresTransaction

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")

if t.TYPE_CHECKING:  # pragma: no cover
    from asyncpg.pool import Pool


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

    def __init__(self, engine: CockroachEngine):
        self.engine = engine
        self.queries: t.List[Query] = []
        super(Atomic, self).__init__(engine)


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

    def __init__(self, engine: CockroachEngine):
        self.engine = engine
        if self.engine.transaction_connection.get():
            raise TransactionError(
                "A transaction is already active - nested transactions aren't "
                "currently supported."
            )
        super(Transaction, self).__init__(engine)


###############################################################################


class CockroachEngine(PostgresEngine):
    """
    An extension of the cockroach backend.
    """

    engine_type = "cockroach"
    min_version_number = 0  # Doesn't seem to work with cockroach versioning.

    def __init__(
        self,
        config: t.Dict[str, t.Any],
        extensions: t.Sequence[str] = (),
        log_queries: bool = False,
        extra_nodes: t.Dict[str, PostgresEngine] = None,
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
        super(
            PostgresEngine, self
        ).__init__()  # lgtm[py/super-not-enclosing-class]

    async def prep_database(self):
        try:
            await self._run_in_new_connection(
                "SET CLUSTER SETTING sql.defaults.experimental_alter_column_type.enabled = true;"  # noqa: E501
            )
        except asyncpg.exceptions.InsufficientPrivilegeError:
            colored_warning(
                "=> Unable to set up Cockroach DB "
                "functionality may not behave as expected. Make sure "
                "your database user has permission to set cluster options.",
                level=Level.medium,
            )
