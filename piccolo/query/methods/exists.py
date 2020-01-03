from __future__ import annotations
import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString

from .select import Select


class Exists(Query):
    __slots__ = ("where_delegate",)

    def _setup_delegates(self):
        self.where_delegate = WhereDelegate()

    def where(self, where: Combinable) -> Exists:
        self.where_delegate.where(where)
        return self

    async def response_handler(self, response) -> bool:
        return response[0]["exists"]

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        select = Select(
            table=self.table,
            base=QueryString(f"SELECT * FROM {self.table._meta.tablename}"),
        )
        select.where_delegate._where = self.where_delegate._where
        return [
            QueryString('SELECT EXISTS({}) AS "exists"', select.querystrings[0])
        ]
