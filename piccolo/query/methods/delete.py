from __future__ import annotations

from piccolo.query.base import Query
from piccolo.query.mixins import WhereMixin
from piccolo.querystring import QueryString


class Delete(Query, WhereMixin):

    @property
    def querystring(self) -> QueryString:
        query = f'DELETE FROM {self.table.Meta.tablename}'
        if self._where:
            query += ' WHERE {}'
            return QueryString(
                query,
                self._where.querystring
            )
        else:
            return QueryString(query)

    def __str__(self) -> str:
        query = f'DELETE FROM {self.table.Meta.tablename}'
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        return query
