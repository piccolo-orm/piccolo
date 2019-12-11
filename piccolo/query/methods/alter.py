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

    column: t.Union[Column, str]

    @property
    def column_name(self) -> str:
        if type(self.column) == str:
            return self.column
        elif isinstance(self.column, Column):
            return self.column._meta.name
        else:
            raise ValueError("Unrecognised column type")

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
            f"RENAME COLUMN {self.column_name} TO {self.new_name}"
        )


@dataclasses.dataclass
class Drop(AlterStatement):
    @property
    def querystring(self) -> QueryString:
        return QueryString(f"DROP {self.column_name}")


@dataclasses.dataclass
class Add(AlterStatement):
    __slots__ = ("name",)

    column: Column
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
            return QueryString(f"ADD UNIQUE ({self.column_name})")
        else:
            tablename = self.column._meta.table._meta.tablename
            column_name = self.column_name
            key = f"{tablename}_{column_name}_key"
            return QueryString(f'DROP CONSTRAINT "{key}"')


@dataclasses.dataclass
class Null(AlterStatement):
    __slots__ = ("boolean",)

    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(f"{self.column_name} DROP NOT NULL")
        else:
            return QueryString(f"{self.column_name} SET NOT NULL")


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
        column._meta._table = self.table
        self._add.append(Add(column, name))
        return self

    def drop_column(self, column: t.Union[str, Column]) -> Alter:
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

    def rename_column(
        self, column: t.Union[str, Column], new_name: str
    ) -> Alter:
        """
        Band.alter().rename_column(Band.popularity, ‘rating’)
        Band.alter().rename_column('popularity', ‘rating’)
        """
        self._rename.append(Rename(column, new_name))
        return self

    def set_null(
        self, column: t.Union[str, Column], boolean: bool = True
    ) -> Alter:
        """
        Band.alter().set_null(Band.name, True)
        Band.alter().set_null('name', True)
        """
        self._null.append(Null(column, boolean))
        return self

    def set_unique(
        self, column: t.Union[str, Column], boolean: bool = True
    ) -> Alter:
        """
        Band.alter().set_unique(Band.name, True)
        Band.alter().set_unique('name', True)
        """
        self._unique.append(Unique(column, boolean))
        return self

    async def response_handler(self, response):
        """
        We don't want to modify the response, but we need to add default values
        to any tables which have had columns added.
        """
        if self._add:
            # If the defaults are just static values then update all of the
            # rows in one go - otherwise we need to update each row at a time.
            # For example, with a UUID field, we need each row to get its
            # own unique value.

            columns = [i.column for i in self._add]

            defaults = [getattr(column, "default", None) for column in columns]

            just_static_defaults = all(
                [hasattr(default, "__call__") for default in defaults]
            )

            tablename = self.table._meta.tablename

            if just_static_defaults:
                for column in columns:
                    await self.table.raw(
                        f"UPDATE {tablename} SET {column._meta.name} = {{}}",
                        column.get_default_value(),
                    ).run()
            else:
                response = await self.table.raw(
                    f"SELECT id from {tablename}"
                ).run()
                ids = [i["id"] for i in response]

                for _id in ids:
                    for column in columns:
                        await self.table.raw(
                            f"UPDATE {tablename} SET {column._meta.name} = {{}} WHERE id = {{}}",
                            column.get_default_value(),
                            _id,
                        ).run()

        return response

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
