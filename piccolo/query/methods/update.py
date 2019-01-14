from piccolo.query.base import Query
from piccolo.query.mixins import WhereMixin
from piccolo.querystring import QueryString


class Update(Query, WhereMixin):

    @property
    def querystring(self) -> QueryString:
        querystring = self.base
        if self._where:
            where_querystring = QueryString(
                '{} WHERE {}',
                querystring,
                self._where.querystring
            )
            return where_querystring
        else:
            return querystring

    def __str__(self) -> str:
        return self.querystring.__str__()
