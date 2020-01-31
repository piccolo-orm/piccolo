from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


@dataclass
class Raw(Query):
    __slots__ = tuple()

    querystring: QueryString

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        return [self.querystring]
