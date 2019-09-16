from __future__ import annotations

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString

from .select import Select


class Count(Query):
    __slots__ = ("where_delegate",)

    def _setup_delegates(self):
        self.where_delegate = WhereDelegate()

    def where(self, where: Combinable) -> Count:
        self.where_delegate.where(where)
        return self

    def response_handler(self, response) -> bool:
        return response[0]["count"]

    @property
    def querystring(self) -> QueryString:
        select = Select(self.table)
        select.where_delegate._where = self.where_delegate._where
        return QueryString(
            'SELECT COUNT(*) AS "count" FROM ({}) AS "subquery"',
            select.querystring,
        )
