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

    __slots__ = ("if_not_exists", "only_default_columns", "auto_create_schema")

    def __init__(
        self,
        table: t.Type[Table],
        if_not_exists: bool = False,
        only_default_columns: bool = False,
        auto_create_schema: bool = True,
        **kwargs,
    ):
        """
        :param table:
            The table to create.
        :param if_not_exists:
            If ``True``, no error will be raised if this table already exists.
        :param only_default_columns:
            If ``True``, just the basic table and default primary key are
            created, rather than all columns. Not typically needed.
        :param auto_create_schema:
            If the table belongs to a database schema, then make sure the
            schema exists before creating the table.

        """
        super().__init__(table, **kwargs)
        self.if_not_exists = if_not_exists
        self.only_default_columns = only_default_columns
        self.auto_create_schema = auto_create_schema

    @property
    def default_ddl(self) -> t.Sequence[str]:
        ddl: t.List[str] = []

        schema_name = self.table._meta.schema
        if (
            self.auto_create_schema
            and schema_name is not None
            and schema_name != "public"
            and self.engine_type != "sqlite"
        ):
            from piccolo.schema import CreateSchema

            ddl.append(
                CreateSchema(
                    schema_name=schema_name,
                    if_not_exists=True,
                    db=self.table._meta.db,
                ).ddl
            )

        prefix = "CREATE TABLE"
        if self.if_not_exists:
            prefix += " IF NOT EXISTS"

        if self.only_default_columns:
            columns = self.table._meta.non_default_columns
        else:
            columns = self.table._meta.columns

        base = f"{prefix} {self.table._meta.get_formatted_tablename()}"
        columns_sql = ", ".join(i.ddl for i in columns)
        ddl.append(f"{base} ({columns_sql})")

        for column in columns:
            if column._meta.index is True:
                ddl.extend(
                    CreateIndex(
                        table=self.table,
                        columns=[column],
                        method=column._meta.index_method,
                        if_not_exists=self.if_not_exists,
                    ).ddl
                )

        return ddl
