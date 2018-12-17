from ..base import Query
from ..mixins import AddMixin


class Insert(Query, AddMixin):

    def run_callback(self, results):
        for index, row in enumerate(results):
            self._add[index].id = row['id']

    def __str__(self):
        base = f'INSERT INTO "{self.table.Meta.tablename}"'
        columns = ','.join(
            [i._name for i in self.table.Meta.columns]
        )
        values = ','.join(
            i.__str__() for i in self._add
        )
        query = f'{base} ({columns}) VALUES {values} RETURNING id'
        return query
