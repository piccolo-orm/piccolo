from __future__ import annotations

import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.methods.select import Count as SelectCount
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


class Count(Query):

    __slots__ = ("where_delegate", "column", "_distinct")

    def __init__(
        self,
        table: t.Type[Table],
        column: t.Optional[Column] = None,
        distinct: t.Optional[t.Sequence[Column]] = None,
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.column = column
        self._distinct = distinct
        self.where_delegate = WhereDelegate()

    ###########################################################################
    # Clauses

    def where(self: Self, *where: Combinable) -> Self:
        self.where_delegate.where(*where)
        return self

    def distinct(self: Self, columns: t.Optional[t.Sequence[Column]]) -> Self:
        self._distinct = columns
        return self

    ###########################################################################

    async def response_handler(self, response) -> bool:
        return response[0]["count"]

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        table: t.Type[Table] = self.table

        query = table.select(
            SelectCount(column=self.column, distinct=self._distinct)
        )

        query.where_delegate._where = self.where_delegate._where

        return query.querystrings


Self = t.TypeVar("Self", bound=Count)
