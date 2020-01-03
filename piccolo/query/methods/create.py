from __future__ import annotations
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Create(Query):
    """
    Creates a database table.
    """

    __slots__: t.Tuple = tuple()

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        base = f"CREATE TABLE {self.table._meta.tablename}"
        columns = ", ".join(["{}" for i in self.table._meta.columns])
        query = f"{base} ({columns})"
        return [
            QueryString(
                query, *[i.querystring for i in self.table._meta.columns]
            )
        ]
