from __future__ import annotations

import typing as t

from piccolo.columns import Column
from piccolo.columns.indexes import IndexMethod
from piccolo.query.base import DDL

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class CreateIndex(DDL):
    def __init__(
        self,
        table: t.Type[Table],
        columns: t.List[t.Union[Column, str]],
        method: IndexMethod = IndexMethod.btree,
        if_not_exists: bool = False,
        **kwargs,
    ):
        self.columns = columns
        self.method = method
        self.if_not_exists = if_not_exists
        super().__init__(table, **kwargs)

    @property
    def column_names(self) -> t.List[str]:
        return [
            i._meta.db_column_name if isinstance(i, Column) else i
            for i in self.columns
        ]

    @property
    def prefix(self) -> str:
        prefix = "CREATE INDEX"
        if self.if_not_exists:
            prefix += " IF NOT EXISTS"
        return prefix

    @property
    def postgres_ddl(self) -> t.Sequence[str]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.tablename
        method_name = self.method.value
        column_names_str = ", ".join([f'"{i}"' for i in self.column_names])
        return [
            (
                f"{self.prefix} {index_name} ON {tablename} USING "
                f"{method_name} ({column_names_str})"
            )
        ]

    @property
    def cockroach_ddl(self) -> t.Sequence[str]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.tablename
        method_name = self.method.value
        column_names_str = ", ".join([f'"{i}"' for i in self.column_names])
        return [
            (
                f"{self.prefix} {index_name} ON {tablename} USING "
                f"{method_name} ({column_names_str})"
            )
        ]

    @property
    def sqlite_ddl(self) -> t.Sequence[str]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.tablename

        method_name = self.method.value
        if method_name != "btree":
            raise ValueError("SQLite only support btree indexes.")

        column_names_str = ", ".join([f'"{i}"' for i in self.column_names])
        return [
            (
                f"{self.prefix} {index_name} ON {tablename} "
                f"({column_names_str})"
            )
        ]
