from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString


@dataclass
class Create(Query):
    """
    Creates a database table.
    """

    __slots__ = tuple()

    if_not_exists: bool = False

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        prefix = "CREATE TABLE"
        if self.if_not_exists:
            prefix += " IF NOT EXISTS"

        base = f"{prefix} {self.table._meta.tablename}"
        columns = ", ".join(["{}" for i in self.table._meta.columns])
        query = f"{base} ({columns})"
        return [
            QueryString(
                query, *[i.querystring for i in self.table._meta.columns]
            )
        ]
