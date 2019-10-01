from __future__ import annotations
import dataclasses
import itertools
import typing as t

from piccolo.columns.base import Column
from piccolo.query.base import Query
from piccolo.querystring import QueryString


@dataclasses.dataclass
class AlterStatement:
    __slots__ = ("column",)

    column: Column

    def querystring(self) -> QueryString:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclasses.dataclass
class Rename(AlterStatement):
    __slots__ = ("new_name",)

    new_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            f"RENAME COLUMN {self.column._meta.name} TO {self.new_name}"
        )


@dataclasses.dataclass
class Drop(AlterStatement):
    @property
    def querystring(self) -> QueryString:
        return QueryString(f"DROP {self.column._meta.name}")


@dataclasses.dataclass
class Add(AlterStatement):
    __slots__ = ("name",)

    name: str

    @property
    def querystring(self) -> QueryString:
        self.column._meta.name = self.name
        return QueryString("ADD {}", self.column.querystring)


@dataclasses.dataclass
class Unique(AlterStatement):
    __slots__ = ("boolean",)

    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(f"ADD UNIQUE ({self.column._meta.name})")
        else:
            tablename = self.column._meta.table._meta.tablename
            column_name = self.column._meta.name
            key = f"{tablename}_{column_name}_key"
            return QueryString(f'DROP CONSTRAINT "{key}"')


@dataclasses.dataclass
class Null(AlterStatement):
    __slots__ = ("boolean",)

    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(f"{self.column._meta.name} DROP NOT NULL")
        else:
            return QueryString(f"{self.column._meta.name} SET NOT NULL")


class Alter(Query):

    __slots__ = ("_add", "_drop", "_rename", "_unique", "_null", "_drop_table")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add: t.List[Add] = []
        self._drop: t.List[Drop] = []
        self._rename: t.List[Rename] = []
        self._unique: t.List[Unique] = []
        self._null: t.List[Null] = []
        self._drop_table = False

    def add_column(self, name: str, column: Column) -> Alter:
        """
        Band.alter().add_column(‘members’, Integer())
        """
        self._add.append(Add(column, name))
        return self

    def drop_column(self, column: Column) -> Alter:
        """
        Band.alter().drop_column(Band.popularity)
        """
        self._drop.append(Drop(column))
        return self

    def drop_table(self) -> Alter:
        """
        Band.alter().drop_table()
        """
        self._drop_table = True
        return self

    def rename_column(self, column: Column, new_name: str) -> Alter:
        """
        Band.alter().rename_column(Band.popularity, ‘rating’)
        """
        self._rename.append(Rename(column, new_name))
        return self

    def set_null(self, column: Column, boolean: bool = True) -> Alter:
        """
        Band.alter().set_null(True)
        """
        self._null.append(Null(column, boolean))
        return self

    def set_unique(self, column: Column, boolean: bool = True) -> Alter:
        """
        Band.alter().set_unique(True)
        """
        self._unique.append(Unique(column, boolean))
        return self

    @property
    def querystring(self) -> QueryString:
        if self._drop_table:
            return QueryString(f'DROP TABLE "{self.table._meta.tablename}"')

        query = f"ALTER TABLE {self.table._meta.tablename}"

        alterations = [
            i.querystring
            for i in itertools.chain(
                self._add, self._rename, self._drop, self._unique, self._null
            )
        ]

        for a in alterations:
            query += " {}"

        return QueryString(query, *alterations)

    def __str__(self) -> str:
        return self.querystring.__str__()
