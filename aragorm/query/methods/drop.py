from ..base import Query


class Drop(Query):

    def __str__(self):
        return f'DROP TABLE "{self.table.Meta.tablename}"'
