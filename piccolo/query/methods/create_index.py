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
        columns: t.List[t.Union[Column, str]],
        method: IndexMethod = IndexMethod.btree,
    ):
        self.columns = columns
        self.method = method
        super().__init__(table)

    @property
    def column_names(self) -> t.List[str]:
        return [
            i._meta.name if isinstance(i, Column) else i for i in self.columns
        ]

    @property
    def postgres_querystrings(self) -> t.Sequence[QueryString]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.tablename
        method_name = self.method.value
        column_names_str = ", ".join(column_names)
        return [
            QueryString(
                f"CREATE INDEX {index_name} ON {tablename} USING {method_name}"
                f" ({column_names_str})"
            )
        ]

    @property
    def sqlite_querystrings(self) -> t.Sequence[QueryString]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.tablename

        method_name = self.method.value
        if method_name != "btree":
            raise ValueError("SQLite only support btree indexes.")

        column_names_str = ", ".join(column_names)
        return [
            QueryString(
                f"CREATE INDEX {index_name} ON {tablename} "
                f"({column_names_str})"
            )
        ]
