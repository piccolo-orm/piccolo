from __future__ import annotations

import typing as t

from piccolo.engine.base import BaseBatch
from piccolo.query.base import Query
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class Raw(Query):
    __slots__ = ("querystring",)

    def __init__(
        self,
        table: t.Type[Table],
        querystring: QueryString = QueryString(""),
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.querystring = querystring

    async def batch(
        self,
        batch_size: t.Optional[int] = None,
        node: t.Optional[str] = None,
        **kwargs,
    ) -> BaseBatch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        if node:
            kwargs.update(node=node)
        return await self.table._meta.db.batch(self, **kwargs)

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        return [self.querystring]
