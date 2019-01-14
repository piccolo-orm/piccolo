from __future__ import annotations

from piccolo.query.base import Query
from piccolo.query.mixins import WhereMixin
from piccolo.querystring import QueryString
from .select import Select


class Exists(Query, WhereMixin):

    @property
    def querystring(self) -> QueryString:
        select = Select(
            self.table,
            QueryString(f'SELECT * FROM {self.table.Meta.tablename}')
        )
        select._where = self._where
        return QueryString('SELECT EXISTS({})', select.querystring)

    def __str__(self) -> str:
        return self.querystring.__str__()
