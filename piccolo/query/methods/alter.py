from __future__ import annotations
import dataclasses
import itertools
import typing as t

from piccolo.columns.base import Column, OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey
from piccolo.query.base import Query
from piccolo.querystring import QueryString


@dataclasses.dataclass
class AlterStatement:
    def querystring(self) -> QueryString:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclasses.dataclass
class AlterColumnStatement(AlterStatement):
    __slots__ = ("column",)

    column: t.Union[Column, str]

    @property
    def column_name(self) -> str:
        if isinstance(self.column, str):
            return self.column
        elif isinstance(self.column, Column):
            return self.column._meta.name
        else:
            raise ValueError("Unrecognised column type")


@dataclasses.dataclass
class RenameColumn(AlterColumnStatement):
    __slots__ = ("new_name",)

    new_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            f"RENAME COLUMN {self.column_name} TO {self.new_name}"
        )


@dataclasses.dataclass
class DropColumn(AlterColumnStatement):
    @property
    def querystring(self) -> QueryString:
        return QueryString(f"DROP COLUMN {self.column_name}")


@dataclasses.dataclass
class AddColumn(AlterColumnStatement):
    __slots__ = ("name",)

    column: Column
    name: str

    @property
    def querystring(self) -> QueryString:
        self.column._meta.name = self.name
        return QueryString("ADD COLUMN {}", self.column.querystring)


@dataclasses.dataclass
class Unique(AlterColumnStatement):
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
class Null(AlterColumnStatement):
    __slots__ = ("boolean",)

    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(
                f"ALTER COLUMN {self.column_name} DROP NOT NULL"
            )
        else:
            return QueryString(f"ALTER COLUMN {self.column_name} SET NOT NULL")


@dataclasses.dataclass
class DropConstraint(AlterStatement):
    __slots__ = ("constraint_name",)

    constraint_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(f"DROP CONSTRAINT IF EXISTS {self.constraint_name}")


@dataclasses.dataclass
class AddForeignKeyConstraint(AlterStatement):
    __slots__ = ("constraint_name",)

    constraint_name: str
    foreign_key_column_name: str
    referenced_table_name: str
    on_delete: t.Optional[OnDelete]
    on_update: t.Optional[OnUpdate]
    referenced_column_name: str = "id"

    @property
    def querystring(self) -> QueryString:
        query = (
            f"ADD CONSTRAINT {self.constraint_name} FOREIGN KEY "
            f"({self.foreign_key_column_name}) REFERENCES "
            f"{self.referenced_table_name} ({self.referenced_column_name})"
        )
        if self.on_delete:
            query += f" ON DELETE {self.on_delete.value}"
        if self.on_update:
            query += f" ON UPDATE {self.on_update.value}"
        return QueryString(query)


class Alter(Query):

    __slots__ = ("_add", "_drop", "_rename", "_unique", "_null", "_drop_table")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add: t.List[AddColumn] = []
        self._drop: t.List[DropColumn] = []
        self._rename: t.List[RenameColumn] = []
        self._unique: t.List[Unique] = []
        self._null: t.List[Null] = []
        self._drop_table = False
        self._drop_contraint: t.List[DropConstraint] = []
        self._add_foreign_key_constraint: t.List[AddForeignKeyConstraint] = []

    def add_column(self, name: str, column: Column) -> Alter:
        """
        Band.alter().add_column(‘members’, Integer())
        """
        column._meta._table = self.table
        self._add.append(AddColumn(column, name))
        return self

    def drop_column(self, column: t.Union[str, Column]) -> Alter:
        """
        Band.alter().drop_column(Band.popularity)
        """
        self._drop.append(DropColumn(column))
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
        self._rename.append(RenameColumn(column, new_name))
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

    def _get_constraint_name(self, column: t.Union[str, ForeignKey]) -> str:
        column_name = AlterColumnStatement(column=column).column_name
        tablename = self.table._meta.tablename
        constraint_name = f"{tablename}_{column_name}_fk"
        return constraint_name

    def drop_constraint(self, constraint_name: str) -> Alter:
        self._drop_contraint.append(
            DropConstraint(constraint_name=constraint_name)
        )
        return self

    def drop_foreign_key_constraint(
        self, column: t.Union[str, ForeignKey]
    ) -> Alter:
        constraint_name = self._get_constraint_name(column=column)
        return self.drop_constraint(constraint_name=constraint_name)

    def add_foreign_key_constraint(
        self,
        column: t.Union[str, ForeignKey],
        referenced_table_name: str,
        on_delete: t.Optional[OnDelete] = None,
        on_update: t.Optional[OnUpdate] = None,
        referenced_column_name: str = "id",
    ) -> Alter:
        """
        This will add a new foreign key constraint.

        Band.alter().add_foreign_key_constraint(
            Band.manager,
            referenced_table_name='manager',
            on_delete=OnDelete.cascade
        )
        """
        constraint_name = self._get_constraint_name(column=column)
        column_name = AlterColumnStatement(column=column).column_name

        self._add_foreign_key_constraint.append(
            AddForeignKeyConstraint(
                constraint_name=constraint_name,
                foreign_key_column_name=column_name,
                referenced_table_name=referenced_table_name,
                on_delete=on_delete,
                on_update=on_update,
                referenced_column_name=referenced_column_name,
            )
        )
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
    def querystrings(self) -> t.Sequence[QueryString]:
        if self._drop_table:
            return [QueryString(f'DROP TABLE "{self.table._meta.tablename}"')]

        query = f"ALTER TABLE {self.table._meta.tablename}"

        alterations = [
            i.querystring
            for i in itertools.chain(
                self._add, self._rename, self._drop, self._unique, self._null
            )
        ]

        if self.engine_type == "sqlite":
            # Can only perform one alter statement at a time.
            query += " {}"
            return [QueryString(query, i) for i in alterations]

        # Postgres can perform them all at once:
        query += ",".join([" {}" for i in alterations])

        return [QueryString(query, *alterations)]
