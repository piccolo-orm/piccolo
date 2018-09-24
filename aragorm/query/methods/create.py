from ..base import Query


class Create(Query):
    """
    Creates a database table.
    """

    def __str__(self):
        base = f'CREATE TABLE "{self.table.Meta.tablename}"'
        columns = ', '.join([i.__str__() for i in self.table.Meta.columns])
        query = f'{base} ({columns})'
        return query
