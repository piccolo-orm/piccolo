from __future__ import annotations

import typing as t
from dataclasses import dataclass

from piccolo.query.base import Query
from piccolo.query.mixins import AddDelegate, ValuesDelegate, WhereDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


@dataclass
class Upsert(Query):
    __slots__ = ("add_delegate", "value_delegate" "where_delegate")

    def __init__(self, table: t.Type[Table], *instances: Table, **kwargs):
        super().__init__(table, **kwargs)
        self.add_delegate = AddDelegate()
        self.value_delegate = ValuesDelegate()
        self.where_delegate = WhereDelegate()
        self.add(*instances)

    def add(self, *instances: Table) -> Upsert:
        self.add_delegate.add(*instances, table_class=self.table)
        return self

    def values(
        self, values: t.Dict[t.Union[Column, str], t.Any] = {}, **kwargs
    ) -> Upsert:
        values = dict(values, **kwargs)
        self.values_delegate.values_update(values)
        return self

    def validator(self, *instances: Table, values: t.Dict[t.Union[Column, str], t.Any] = {}):
        if self.where_delegate.response_handler(self) == False:
            self.add_delegate.add(*instances, table_class=self.table)
        else:
            self.values_delegate.values_update(values)

    def run_callback(self, results):
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
        columns = ",".join([i._meta.name for i in self.table._meta.columns])
        print(columns)
        values = ",".join(["{}" for _ in self.add_delegate._add])
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
            [f'"{i._meta.name}"' for i in self.table._meta.columns]
        )
        values = ",".join(["{}" for i in self.add_delegate._add])
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
