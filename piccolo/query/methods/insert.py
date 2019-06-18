from __future__ import annotations

from piccolo.query.base import Query
from piccolo.query.mixins import AddMixin
from piccolo.querystring import QueryString


class Insert(Query, AddMixin):

    def run_callback(self, results):
        """
        Assign the ids of the created rows to the model instances.
        """
        for index, row in enumerate(results):
            self._add[index].id = row['id']

    @property
    def sqlite_querystring(self) -> QueryString:
        if len(self._add) > 1:
            raise Exception(
                "The SQLite engine is unable to insert more than one row at a "
                "time."
            )

        base = f'INSERT INTO {self.table.Meta.tablename}'
        columns = ','.join(
            [i._name for i in self.table.Meta.columns]
        )
        values = ','.join([
            '{}' for i in self._add
        ])
        query = f'{base} ({columns}) VALUES {values}'
        return QueryString(
            query,
            *[i.querystring for i in self._add],
            query_type='insert'
        )

    @property
    def postgres_querystring(self) -> QueryString:
        base = f'INSERT INTO {self.table.Meta.tablename}'
        columns = ','.join(
            [i._name for i in self.table.Meta.columns]
        )
        values = ','.join([
            '{}' for i in self._add
        ])
        query = f'{base} ({columns}) VALUES {values} RETURNING id'
        return QueryString(
            query,
            *[i.querystring for i in self._add],
            query_type='insert'
        )
