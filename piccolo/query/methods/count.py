from __future__ import annotations

import typing as t

from piccolo.columns import Column
from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import DistinctDelegate, WhereDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class Count(Query):
    __slots__ = (
        "where_delegate",
        "distinct_delegate",
    )

    def __init__(self, table: t.Type[Table], **kwargs):
        super().__init__(table, **kwargs)
        self.where_delegate = WhereDelegate()
        self.distinct_delegate = DistinctDelegate()

    ###########################################################################
    # Clauses

    def where(self: Self, *where: Combinable) -> Self:
        self.where_delegate.where(*where)
        return self

    def distinct(
        self: Self, *, on: t.Optional[t.Sequence[Column]] = None
    ) -> Self:
        if on is not None and self.engine_type == "sqlite":
            raise NotImplementedError("SQLite doesn't support DISTINCT ON")

        self.distinct_delegate.distinct(enabled=True, on=on)
        return self

    ###########################################################################

    async def response_handler(self, response) -> bool:
        return response[0]["count"]

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        select = Select(self.table)
        select.where_delegate._where = self.where_delegate._where
        select.distinct_delegate._distinct = self.distinct_delegate._distinct
        return [
            QueryString(
                'SELECT COUNT(*) AS "count" FROM ({}) AS "subquery"',
                select.querystrings[0],
            )
        ]


Self = t.TypeVar("Self", bound=Count)
