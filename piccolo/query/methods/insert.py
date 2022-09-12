from __future__ import annotations

import typing as t

from piccolo.query.base import Query
from piccolo.query.mixins import AddDelegate, ReturningDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Column
    from piccolo.table import Table


class Insert(Query):
    __slots__ = ("add_delegate", "returning_delegate")

    def __init__(self, table: t.Type[Table], *instances: Table, **kwargs):
        super().__init__(table, **kwargs)
        self.add_delegate = AddDelegate()
        self.returning_delegate = ReturningDelegate()
        self.add(*instances)

    ###########################################################################
    # Clauses

    def add(self, *instances: Table) -> Insert:
        self.add_delegate.add(*instances, table_class=self.table)
        return self

    def returning(self, *columns: Column) -> Insert:
        self.returning_delegate.returning(columns)
        return self

    ###########################################################################

    def _raw_response_callback(self, results):
        """
        Assign the ids of the created rows to the model instances.
        """
        for index, row in enumerate(results):
            table_instance: Table = self.add_delegate._add[index]
            setattr(
                table_instance,
                self.table._meta.primary_key._meta.name,
                row.get(
                    self.table._meta.primary_key._meta.db_column_name, None
                ),
            )
            table_instance._exists_in_db = True

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        base = f'INSERT INTO "{self.table._meta.tablename}"'
        columns = ",".join(
            f'"{i._meta.db_column_name}"' for i in self.table._meta.columns
        )
        values = ",".join("{}" for _ in self.add_delegate._add)
        query = f"{base} ({columns}) VALUES {values}"
        querystring = QueryString(
            query,
            *[i.querystring for i in self.add_delegate._add],
            query_type="insert",
            table=self.table,
        )

        engine_type = self.engine_type

        if engine_type in ("postgres", "cockroach") or (
            engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() >= 3.35
        ):
            if self.returning_delegate._returning:
                return [
                    QueryString(
                        "{}{}",
                        querystring,
                        self.returning_delegate._returning.querystring,
                        query_type="insert",
                        table=self.table,
                    )
                ]

        return [querystring]
