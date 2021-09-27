from __future__ import annotations

import typing as t

from piccolo.query.base import DDL
from piccolo.query.methods.create_index import CreateIndex

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class Create(DDL):
    """
    Creates a database table.
    """

    __slots__ = ("if_not_exists", "only_default_columns")

    def __init__(
        self,
        table: t.Type[Table],
        if_not_exists: bool = False,
        only_default_columns: bool = False,
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.if_not_exists = if_not_exists
        self.only_default_columns = only_default_columns

    @property
    def default_ddl(self) -> t.Sequence[str]:
        prefix = "CREATE TABLE"
        if self.if_not_exists:
            prefix += " IF NOT EXISTS"

        if self.only_default_columns:
            columns = self.table._meta.non_default_columns
        else:
            columns = self.table._meta.columns

        base = f"{prefix} {self.table._meta.tablename}"
        columns_sql = ", ".join(i.ddl for i in columns)
        create_table_ddl = f"{base} ({columns_sql})"

        create_indexes: t.List[str] = []
        for column in columns:
            if column._meta.index is True:
                create_indexes.extend(
                    CreateIndex(
                        table=self.table,
                        columns=[column],
                        method=column._meta.index_method,
                        if_not_exists=self.if_not_exists,
                    ).ddl
                )

        return [create_table_ddl] + create_indexes
