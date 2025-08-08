from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional

from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.warnings import Level, colored_warning

from .postgres import PostgresEngine

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")


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
