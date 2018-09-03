import dataclasses

from .columns import Column
from .query import Query


@dataclasses.dataclass
class Rename():
    """
    Pokemon.alter().rename(Pokemon.power, ‘rating’)
    """
    column: Column
    new_name: str

    def __str__(self):
        return f' RENAME {self.column.name} TO {self.new_name}'


@dataclasses.dataclass
class Drop():
    """
    Pokemon.alter().drop(Pokemon.power, ‘rating’)
    """
    column: Column

    def __str__(self):
        return f' DROP {self.column.name}'


@dataclasses.dataclass
class Add():
    """
    Pokemon.alter().add(‘color’, Varchar(length=20))
    """
    name: str
    column: Column

    def __str__(self):
        self.column.name = self.name
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
        query = self.base
        for alterations in [self._add, self._rename, self._drop]:
            for a in alterations:
                query += a.__str__()
        return query
