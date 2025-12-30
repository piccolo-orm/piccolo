from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from piccolo.utils.lazy_loader import LazyLoader

from .postgres import PostgresEngine

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")

if TYPE_CHECKING:  # pragma: no cover
    from asyncpg.connection import Connection


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

    async def get_new_connection(self) -> Connection:
        """
        Set `autocommit_before_ddl` to off (enabled by default since v25.2)
        to prevent automatic DDL commits in transactions and enable rollback
        """
        connection = await super().get_new_connection()
        await connection.execute(
            "SET autocommit_before_ddl = off;"
            "ALTER ROLE ALL SET autocommit_before_ddl = false;"
        )
        return connection
