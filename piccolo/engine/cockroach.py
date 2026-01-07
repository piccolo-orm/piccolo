from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional

from .postgres import PostgresEngine, PostgresTransaction


class CockroachTransaction(PostgresTransaction):
    async def begin(self):
        await self.transaction.start()
        # Set `autocommit_before_ddl` to off (enabled by default since v25.2)
        # to prevent automatic DDL commits in transactions and enable rollback.
        # Applies only to the current transaction and automatically reverted
        # when the transaction commits or rollback.
        await self.connection.execute("SET LOCAL autocommit_before_ddl = off")


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

    def transaction(self, allow_nested: bool = True) -> CockroachTransaction:
        return CockroachTransaction(engine=self, allow_nested=allow_nested)
