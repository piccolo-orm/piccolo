from __future__ import annotations

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Drop(Query):

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            f'DROP TABLE "{self.table.Meta.tablename}"'
        )

    def __str__(self) -> str:
        return self.querystring.__str__()
