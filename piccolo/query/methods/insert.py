from __future__ import annotations

import typing as t

from piccolo.query.base import Query
from piccolo.query.mixins import AddDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class Insert(Query):
    __slots__ = ("add_delegate",)

    def __init__(self, table: t.Type[Table], *instances: Table, **kwargs):
        super().__init__(table, **kwargs)
        self.add_delegate = AddDelegate()
        self.add(*instances)

    def add(self, *instances: Table) -> Insert:
        self.add_delegate.add(*instances, table_class=self.table)
        return self

    def run_callback(self, results):
        """
        Assign the ids of the created rows to the model instances.
        """
        for index, row in enumerate(results):
            table_instance: Table = self.add_delegate._add[index]
            setattr(
                table_instance,
                self.table._meta.primary_key._meta.name,
                row[self.table._meta.primary_key._meta.name],
            )
            table_instance._exists_in_db = True

    @property
    def sqlite_querystrings(self) -> t.Sequence[QueryString]:
        base = f"INSERT INTO {self.table._meta.tablename}"
        columns = ",".join(
            f'"{i._meta.db_column_name}"' for i in self.table._meta.columns
        )
        values = ",".join("{}" for _ in self.add_delegate._add)
        query = f"{base} ({columns}) VALUES {values}"
        return [
            QueryString(
                query,
                *[i.querystring for i in self.add_delegate._add],
                query_type="insert",
                table=self.table,
            )
        ]

    @property
    def postgres_querystrings(self) -> t.Sequence[QueryString]:
        base = f"INSERT INTO {self.table._meta.tablename}"
        columns = ",".join(
            f'"{i._meta.db_column_name}"' for i in self.table._meta.columns
        )
        values = ",".join("{}" for _ in self.add_delegate._add)
        primary_key_name = self.table._meta.primary_key._meta.name
        query = (
            f"{base} ({columns}) VALUES {values} RETURNING {primary_key_name}"
        )
        return [
            QueryString(
                query,
                *[i.querystring for i in self.add_delegate._add],
                query_type="insert",
            )
        ]
