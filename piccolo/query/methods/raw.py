from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from piccolo.table import Table


@dataclass
class Raw(Query):
    __slots__ = ("querystring",)

    def __init__(
        self, table: t.Type[Table], querystring: QueryString = QueryString("")
    ):
        super().__init__(table)
        self.querystring = querystring

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        return [self.querystring]
