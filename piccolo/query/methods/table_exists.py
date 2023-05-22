from __future__ import annotations

import typing as t

from piccolo.custom_types import TableInstance
from piccolo.query.base import Query
from piccolo.querystring import QueryString


class TableExists(Query[TableInstance, bool]):

    __slots__: t.Tuple = ()

    async def response_handler(self, response):
        return bool(response[0]["exists"])

    @property
    def sqlite_querystrings(self) -> t.Sequence[QueryString]:
        return [
            QueryString(
                "SELECT EXISTS(SELECT * FROM sqlite_master WHERE "
                "name = {}) AS 'exists'",
                self.table._meta.tablename,
            )
        ]

    @property
    def postgres_querystrings(self) -> t.Sequence[QueryString]:
        subquery = QueryString(
            "SELECT * FROM information_schema.tables WHERE table_name = {}",
            self.table._meta.tablename,
        )

        if self.table._meta.schema:
            subquery = QueryString(
                "{} AND table_schema = {}", subquery, self.table._meta.schema
            )

        query = QueryString("SELECT EXISTS({})", subquery)

        return [query]

    @property
    def cockroach_querystrings(self) -> t.Sequence[QueryString]:
        return self.postgres_querystrings
