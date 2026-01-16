from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional

from piccolo.query.base import DDL, Query

from .postgres import Atomic, PostgresEngine, PostgresTransaction


class CockroachAtomic(Atomic):
    """
    :param autocommit_before_ddl:
        Default to ``False`` to prevent automatic DDL commits
        in transactions and enable rollback.
        Applies only to the current transaction and automatically
        reverted when the transaction commits or rollback.

    Usage::

        # Default to ``False`` (``autocommit_before_ddl = off``)
        transaction = engine.atomic()
        transaction.add(Foo.create_table())

        # If we want set ``autocommit_before_ddl = on``
        # which is default Cockroach session setting.
        transaction = engine.atomic(autocommit_before_ddl=True)
        transaction.add(Foo.create_table())

    """

    __slots__ = ("autocommit_before_ddl",)

    def __init__(
        self,
        engine: CockroachEngine,
        autocommit_before_ddl: Optional[bool] = False,
    ):
        super().__init__(engine)
        self.autocommit_before_ddl = autocommit_before_ddl

    async def run(self):
        from piccolo.query.methods.objects import Create, GetOrCreate

        try:
            async with self.engine.transaction(
                autocommit_before_ddl=self.autocommit_before_ddl
            ):
                for query in self.queries:
                    if isinstance(query, (Query, DDL, Create, GetOrCreate)):
                        await query.run()
                    else:
                        raise ValueError("Unrecognised query")

            self.queries = []

        except Exception as exception:
            self.queries = []
            raise exception from exception


class CockroachTransaction(PostgresTransaction):
    """
    :param autocommit_before_ddl:
        Default to ``False`` to prevent automatic DDL commits
        in transactions and enable rollback. Applies only
        to the current transaction and automatically
        reverted when the transaction commits or rollback.

    Usage::

        # Default to ``False`` (``autocommit_before_ddl = off``)
        async with engine.transaction():
            # Run some queries:
            await Band.select().run()

        # If we want set ``autocommit_before_ddl = on``
        # which is default Cockroach session setting.
        async with engine.transaction(autocommit_before_ddl=True):
            # Run some queries:
            await Band.select().run()

    """

    __slots__ = ("autocommit_before_ddl",)

    def __init__(
        self,
        autocommit_before_ddl: Optional[bool] = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.autocommit_before_ddl = autocommit_before_ddl

    async def begin(self):
        await self.transaction.start()

        value = "on" if self.autocommit_before_ddl else "off"
        await self.connection.execute(
            f"SET LOCAL autocommit_before_ddl = {value}"
        )


class CockroachEngine(PostgresEngine):
    """
    An extension of
    :class:`PostgresEngine <piccolo.engine.postgres.PostgresEngine>`.
    """

    def __init__(
        self,
        config: dict[str, Any],
        extensions: Sequence[str] = (),
        log_queries: bool = False,
        log_responses: bool = False,
        extra_nodes: Optional[dict[str, CockroachEngine]] = None,
    ) -> None:
        super().__init__(
            config=config,
            extensions=extensions,
            log_queries=log_queries,
            log_responses=log_responses,
            extra_nodes=extra_nodes,
        )
        self.engine_type = "cockroach"
        self.min_version_number = 0

    def atomic(
        self,
        autocommit_before_ddl: Optional[bool] = False,
    ) -> CockroachAtomic:
        return CockroachAtomic(
            engine=self,
            autocommit_before_ddl=autocommit_before_ddl,
        )

    def transaction(
        self,
        allow_nested: bool = True,
        autocommit_before_ddl: Optional[bool] = False,
    ) -> CockroachTransaction:
        return CockroachTransaction(
            engine=self,
            allow_nested=allow_nested,
            autocommit_before_ddl=autocommit_before_ddl,
        )
