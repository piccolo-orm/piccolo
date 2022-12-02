from __future__ import annotations

import typing as t

from piccolo.utils.lazy_loader import LazyLoader
from piccolo.utils.warnings import Level, colored_warning

from .postgres import PostgresEngine

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")


class CockroachEngine(PostgresEngine):
    """
    An extension of
    :class:`PostgresEngine <piccolo.engine.postgres.PostgresEngine>`.
    """

    engine_type = "cockroach"
    min_version_number = 0  # Doesn't seem to work with cockroach versioning.

    def __init__(
        self,
        config: t.Dict[str, t.Any],
        extensions: t.Sequence[str] = (),
        log_queries: bool = False,
        extra_nodes: t.Dict[str, CockroachEngine] = None,
    ) -> None:
        super().__init__(
            config=config,
            extensions=extensions,
            log_queries=log_queries,
            extra_nodes=extra_nodes,
        )

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
