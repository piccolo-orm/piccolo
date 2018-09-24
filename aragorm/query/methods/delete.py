from ..base import Query
from ..mixins import WhereMixin


class Delete(Query, WhereMixin):

    def __str__(self):
        query = f'DELETE FROM {self.table.Meta.tablename}'
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        return query
