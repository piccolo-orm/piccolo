from __future__ import annotations

from piccolo.query.base import Query
from piccolo.querystring import QueryString


class Raw(Query):

    @property
    def querystring(self) -> QueryString:
        return self.base

    def __str__(self):
        return self.querystring.__str__()
