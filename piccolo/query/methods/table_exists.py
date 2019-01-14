from __future__ import annotations

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class TableExists(Query):

    def response_handler(self, response):
        return response[0]['exists']

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE "
            f"table_name = '{self.table.Meta.tablename}')"
        )

    def __str__(self) -> str:
        return self.querystring.__str__()
