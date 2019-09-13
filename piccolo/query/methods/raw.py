from __future__ import annotations
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Raw(Query):
    __slots__: t.Tuple = tuple()

    @property
    def querystring(self) -> QueryString:
        return self.base
