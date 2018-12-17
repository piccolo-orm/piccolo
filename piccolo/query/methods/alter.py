import dataclasses

from piccolo.columns.base import Column
from ..base import Query


@dataclasses.dataclass
class Rename():
    """
    Band.alter.rename(Band.popularity, ‘rating’)
    """
    column: Column
    new_name: str

    def __str__(self):
        return f' RENAME "{self.column._name}" TO "{self.new_name}"'


@dataclasses.dataclass
class Drop():
    """
    Band.alter.drop('popularity')
    """
    column: Column

    def __str__(self):
        return f' DROP "{self.column._name}"'


@dataclasses.dataclass
class Add():
    """
    Band.alter.add(‘members’, Integer())
    """
    name: str
    column: Column

    def __str__(self):
        self.column._name = self.name
        return f' ADD {self.column.__str__()}'


class Alter(Query):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add = []
        self._drop = []
        self._rename = []

    def add(self, name: str, column: Column):
        self._add.append(
            Add(name, column)
        )
        return self

    def rename(self, column: Column, new_name: str):
        self._rename.append(
            Rename(column, new_name)
        )
        return self

    def drop(self, column: Column):
        self._drop.append(
            Drop(column)
        )
        return self

    def __str__(self):
        query = f'ALTER TABLE "{self.table.Meta.tablename}"'
        for alterations in [self._add, self._rename, self._drop]:
            for a in alterations:
                query += a.__str__()
        return query
