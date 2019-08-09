from __future__ import annotations
import dataclasses
import itertools

from piccolo.columns.base import Column
from piccolo.query.base import Query
from piccolo.querystring import QueryString


@dataclasses.dataclass
class Rename():
    column: Column
    new_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            f'RENAME {self.column._name} TO {self.new_name}',
        )

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclasses.dataclass
class Drop():
    column: Column

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            f'DROP {self.column._name}'
        )

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclasses.dataclass
class Add():
    name: str
    column: Column

    @property
    def querystring(self) -> QueryString:
        self.column._name = self.name
        return QueryString(
            'ADD {}',
            self.column.querystring
        )

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclasses.dataclass
class Unique():
    column: Column
    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(
                f'ADD UNIQUE ({self.column._name})'
            )
        else:
            key = f'{self.column._table.Meta.tablename}_{self.column._name}_key'
            return QueryString(
                f'DROP CONSTRAINT "{key}"'
            )

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclasses.dataclass
class Null():
    column: Column
    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(
                f'{self.column._name} DROP NOT NULL'
            )
        else:
            return QueryString(
                f'{self.column._name} SET NOT NULL'
            )

    def __str__(self) -> str:
        return self.querystring.__str__()


class Alter(Query):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add: t.List[Add] = []
        self._drop: t.List[Drop] = []
        self._rename: t.List[Rename] = []
        self._unique: t.List[Unique] = []
        self._null: t.List[Null] = []

    def add_column(self, name: str, column: Column) -> Alter:
        """
        Band.alter().add_column(‘members’, Integer())
        """
        self._add.append(
            Add(name, column)
        )
        return self

    def rename_column(self, column: Column, new_name: str) -> Alter:
        """
        Band.alter().rename_column(Band.popularity, ‘rating’)
        """
        self._rename.append(
            Rename(column, new_name)
        )
        return self

    def drop_column(self, column: Column) -> Alter:
        """
        Band.alter().drop_column('popularity')
        """
        self._drop.append(
            Drop(column)
        )
        return self

    def set_unique(self, column: Column, boolean: bool = True) -> Alter:
        """
        Band.alter().set_unique(True)
        """
        self._unique.append(
            Unique(column, boolean)
        )
        return self

    def set_null(self, column: Column, boolean: bool = True) -> Alter:
        """
        Band.alter().set_null(True)
        """
        self._null.append(
            Unique(column, boolean)
        )
        return self

    @property
    def querystring(self) -> QueryString:
        query = f'ALTER TABLE {self.table.Meta.tablename}'

        alterations = [
            i.querystring for i in itertools.chain(
                self._add,
                self._rename,
                self._drop,
                self._unique,
                self._null
            )
        ]

        for a in alterations:
            query += ' {}'

        return QueryString(
            query,
            *alterations
        )

    def __str__(self) -> str:
        return self.querystring.__str__()
