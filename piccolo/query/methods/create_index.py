from __future__ import annotations
from enum import Enum
import typing as t

from piccolo.columns import Column
from piccolo.query.base import Query
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from piccolo.table import Table


class IndexMethod(str, Enum):
    btree = "btree"
    hash = "hash"
    gist = "gist"
    gin = "gin"


class CreateIndex(Query):
    def __init__(
        self,
        table: t.Type[Table],
        column: Column,
        method: IndexMethod = IndexMethod.btree,
    ):
        self.column = column
        self.method = method
        super().__init__(table)

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        index_name = self.column._meta.index_name
        tablename = self.table._meta.tablename
        method_name = self.method.value
        return [
            QueryString(
                f"CREATE INDEX {index_name} ON {tablename} USING {method_name}"
                f" ({self.column._meta.name})"
            )
        ]
