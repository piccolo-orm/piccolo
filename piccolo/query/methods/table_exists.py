from __future__ import annotations
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class TableExists(Query):

    __slots__: t.Tuple = tuple()

    def response_handler(self, response):
        return bool(response[0]["exists"])

    @property
    def sqlite_querystring(self) -> QueryString:
        return QueryString(
            "SELECT EXISTS(SELECT * FROM sqlite_master WHERE "
            f"name = '{self.table._meta.tablename}') AS 'exists'"
        )

    @property
    def postgres_querystring(self) -> QueryString:
        return QueryString(
            "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE "
            f"table_name = '{self.table._meta.tablename}')"
        )

    def __str__(self) -> str:
        return self.querystring.__str__()
