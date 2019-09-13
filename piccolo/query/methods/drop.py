from __future__ import annotations
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Drop(Query):

    __slots__: t.Tuple = tuple()

    @property
    def querystring(self) -> QueryString:
        return QueryString(f'DROP TABLE "{self.table._meta.tablename}"')

    def __str__(self) -> str:
        return self.querystring.__str__()
