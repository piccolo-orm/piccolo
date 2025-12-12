from __future__ import annotations

from collections.abc import Sequence

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Indexes(Query):
    """
    Returns the indexes for the given table.
    """

    @property
    def postgres_querystrings(self) -> Sequence[QueryString]:
        return [
            QueryString(
                "SELECT indexname AS name FROM pg_indexes "
                "WHERE tablename = {}",
                self.table._meta.get_formatted_tablename(quoted=False),
            )
        ]

    @property
    def cockroach_querystrings(self) -> Sequence[QueryString]:
        return self.postgres_querystrings

    @property
    def sqlite_querystrings(self) -> Sequence[QueryString]:
        tablename = self.table._meta.tablename
        return [QueryString(f"PRAGMA index_list({tablename})")]

    @property
    def mysql_querystrings(self) -> Sequence[QueryString]:
        return [
            QueryString(
                "SELECT DISTINCT INDEX_NAME AS name "
                "FROM INFORMATION_SCHEMA.STATISTICS "
                "WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = {}",
                self.table._meta.get_formatted_tablename(quoted=False),
            )
        ]

    async def response_handler(self, response):
        return [i["name"] for i in response]
