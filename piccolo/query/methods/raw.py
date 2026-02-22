from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

from piccolo.engine.base import BaseBatch
from piccolo.query.base import Query
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class Raw(Query):
    __slots__ = ("querystring",)

    def __init__(
        self,
        table: type[Table],
        querystring: QueryString = QueryString(""),
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.querystring = querystring

    async def batch(
        self,
        batch_size: Optional[int] = None,
        node: Optional[str] = None,
        **kwargs,
    ) -> BaseBatch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        if node:
            kwargs.update(node=node)
        return await self.table._meta.db.batch(self, **kwargs)

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        return [self.querystring]
