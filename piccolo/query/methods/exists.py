from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar, Union

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString


class Exists(Query[TableInstance, bool]):
    __slots__ = ("where_delegate",)

    def __init__(self, table: type[TableInstance], **kwargs):
        super().__init__(table, **kwargs)
        self.where_delegate = WhereDelegate()

    def where(self: Self, *where: Union[Combinable, QueryString]) -> Self:
        self.where_delegate.where(*where)
        return self

    async def response_handler(self, response) -> bool:
        # Convert to a bool - postgres returns True, and sqlite return 1.
        return bool(response[0]["exists"])

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        select = Select(table=self.table)
        select.where_delegate._where = self.where_delegate._where
        return [
            QueryString(
                'SELECT EXISTS({}) AS "exists"', select.querystrings[0]
            )
        ]


Self = TypeVar("Self", bound=Exists)
