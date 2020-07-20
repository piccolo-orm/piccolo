from __future__ import annotations
import typing as t

from piccolo.query.base import Query
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from piccolo.columns.base import Column
    from piccolo.table import Table


class DropIndex(Query):
    def __init__(self, table: t.Type[Table], column: Column):
        self.column = column
        super().__init__(table)

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        index_name = self.column._meta.index_name
        return [QueryString(f"DROP INDEX {index_name}")]
