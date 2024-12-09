from __future__ import annotations

import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Indexes(Query):
    """
    Returns the indexes for the given table.
    """

    @property
    def postgres_querystrings(self) -> t.Sequence[QueryString]:
        return [
            QueryString(
                "SELECT indexname AS name FROM pg_indexes "
                "WHERE tablename = {}",
                self.table._meta.get_formatted_tablename(quoted=False),
            )
        ]

    @property
    def cockroach_querystrings(self) -> t.Sequence[QueryString]:
        return self.postgres_querystrings

    @property
    def sqlite_querystrings(self) -> t.Sequence[QueryString]:
        tablename = self.table._meta.tablename
        return [QueryString(f"PRAGMA index_list({tablename})")]

    async def response_handler(self, response):
        return [i["name"] for i in response]
