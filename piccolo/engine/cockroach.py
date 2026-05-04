from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional, cast

from .postgres import Atomic, PostgresEngine, PostgresTransaction


class CockroachAtomic(Atomic):

    __slots__ = ("autocommit_before_ddl",)

    def __init__(
        self,
        engine: CockroachEngine,
        autocommit_before_ddl: Optional[bool] = False,
    ):
        """
        :param autocommit_before_ddl:
            Defaults to ``False`` to prevent automatic DDL commits
            in transactions (preventing rollbacks). Applies only to the current
            transaction and is automatically reverted when the transaction
            commits or is rolled back.

            Usage::

                # Defaults to ``False`` (``autocommit_before_ddl = off``)
                transaction = engine.atomic()
                transaction.add(Foo.create_table())

                # If we want to set ``autocommit_before_ddl = on``,
                # which is the default Cockroach session setting.
                transaction = engine.atomic(autocommit_before_ddl=True)
                transaction.add(Foo.create_table())

        """
        super().__init__(engine)
        self.autocommit_before_ddl = autocommit_before_ddl

    async def setup_transaction(self, transaction: PostgresTransaction):
        if self.autocommit_before_ddl is not None:
            transaction = cast(CockroachTransaction, transaction)
            await transaction.autocommit_before_ddl(
                enabled=self.autocommit_before_ddl
            )


class CockroachTransaction(PostgresTransaction):

    async def autocommit_before_ddl(self, enabled: bool = True):
        value = "on" if enabled else "off"
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
    ) -> CockroachTransaction:
        return CockroachTransaction(
            engine=self,
            allow_nested=allow_nested,
        )
