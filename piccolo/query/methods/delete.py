from __future__ import annotations

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString


class Delete(Query):

    def setup_delegates(self):
        self.where_delegate = WhereDelegate()

    def where(self, where: Combinable) -> Delete:
        self.where_delegate.where(where)
        return self

    @property
    def querystring(self) -> QueryString:
        query = f'DELETE FROM {self.table.Meta.tablename}'
        if self.where_delegate._where:
            query += ' WHERE {}'
            return QueryString(
                query,
                self.where_delegate._where.querystring
            )
        else:
            return QueryString(query)

    def __str__(self) -> str:
        query = f'DELETE FROM {self.table.Meta.tablename}'
        if self.where_delegate._where:
            query += f' WHERE {self.where_delegate._where.__str__()}'
        return query
