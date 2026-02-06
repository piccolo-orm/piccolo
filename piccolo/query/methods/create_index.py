from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional, Union

from piccolo.columns import Column
from piccolo.columns.indexes import IndexMethod
from piccolo.query.base import DDL

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class CreateIndex(DDL):
    def __init__(
        self,
        table: type[Table],
        columns: Union[list[Column], list[str]],
        method: IndexMethod = IndexMethod.btree,
        if_not_exists: bool = False,
        name: Optional[str] = None,
        **kwargs,
    ):
        self.columns = columns
        self.method = method
        self.if_not_exists = if_not_exists
        self.name = name
        super().__init__(table, **kwargs)

    @property
    def column_names(self) -> list[str]:
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
    def postgres_ddl(self) -> Sequence[str]:
        column_names = self.column_names
        if self.name is not None:
            index_name = self.name
        else:
            index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.get_formatted_tablename()
        method_name = self.method.value
        column_names_str = ", ".join([f'"{i}"' for i in self.column_names])
        return [
            (
                f"{self.prefix} {index_name} ON {tablename} USING "
                f"{method_name} ({column_names_str})"
            )
        ]

    @property
    def cockroach_ddl(self) -> Sequence[str]:
        return self.postgres_ddl

    @property
    def sqlite_ddl(self) -> Sequence[str]:
        column_names = self.column_names
        if self.name is not None:
            index_name = self.name
        else:
            index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.get_formatted_tablename()

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
