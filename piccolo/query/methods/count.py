from __future__ import annotations

import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


class Count(Query):

    __slots__ = ("where_delegate", "distinct")

    def __init__(
        self,
        table: t.Type[Table],
        distinct: t.Optional[t.Sequence[Column]] = None,
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.distinct = distinct
        self.where_delegate = WhereDelegate()

    ###########################################################################
    # Clauses

    def where(self: Self, *where: Combinable) -> Self:
        self.where_delegate.where(*where)
        return self

    ###########################################################################

    async def response_handler(self, response) -> bool:
        return response[0]["count"]

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        select = Select(self.table)
        select.where_delegate._where = self.where_delegate._where

        base: str

        if self.distinct:
            if len(self.distinct) > 1:
                column_names = ", ".join(
                    f'"{i._meta.db_column_name}"' for i in self.distinct
                )
                base = f"SELECT COUNT(DISTINCT ({column_names}))"
            else:
                column_name = self.distinct[0]._meta.db_column_name
                base = f'SELECT COUNT(DISTINCT "{column_name}")'
        else:
            base = "SELECT COUNT (*)"

        return [
            QueryString(
                base + ' AS "count" FROM ({}) AS "subquery"',
                select.querystrings[0],
            )
        ]


Self = t.TypeVar("Self", bound=Count)
