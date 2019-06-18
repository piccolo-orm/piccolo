from __future__ import annotations

from piccolo.query.base import Query
from piccolo.query.mixins import AddMixin
from piccolo.querystring import QueryString


class Insert(Query, AddMixin):

    def run_callback(self, results):
        for index, row in enumerate(results):
            self._add[index].id = row['id']

    @property
    def querystring(self) -> QueryString:
        # To make this work, can just omit the primary key field for now?
        base = f'INSERT INTO {self.table.Meta.tablename}'
        columns = ','.join(
            [i._name for i in self.table.Meta.non_default_columns]
        )
        values = ','.join([
            '{}' for i in self._add
        ])
        # query = f'{base} ({columns}) VALUES {values} RETURNING id'
        query = f'{base} ({columns}) VALUES {values}'
        return QueryString(
            query,
            *[i.querystring for i in self._add]
        )

    def __str__(self) -> str:
        return self.querystring.__str__()
