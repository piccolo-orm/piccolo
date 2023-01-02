from __future__ import annotations

import typing as t

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString


class Exists(Query[TableInstance, bool]):
    __slots__ = ("where_delegate",)

    def __init__(self, table: t.Type[TableInstance], **kwargs):
        super().__init__(table, **kwargs)
        self.where_delegate = WhereDelegate()

    def where(self: Self, *where: Combinable) -> Self:
        self.where_delegate.where(*where)
        return self

    async def response_handler(self, response) -> bool:
        # Convert to a bool - postgres returns True, and sqlite return 1.
        return bool(response[0]["exists"])

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        select = Select(table=self.table)
        select.where_delegate._where = self.where_delegate._where
        return [
            QueryString(
                'SELECT EXISTS({}) AS "exists"', select.querystrings[0]
            )
        ]


Self = t.TypeVar("Self", bound=Exists)
