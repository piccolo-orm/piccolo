from __future__ import annotations
from dataclasses import dataclass
import itertools
import typing as t

from piccolo.columns.base import Column, OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey, Varchar, Numeric
from piccolo.query.base import Query
from piccolo.querystring import QueryString
from piccolo.utils.warnings import colored_warning, Level

if t.TYPE_CHECKING:
    from piccolo.table import Table


@dataclass
class AlterStatement:
    __slots__ = tuple()  # type: ignore

    def querystring(self) -> QueryString:
        raise NotImplementedError()

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class RenameTable(AlterStatement):
    __slots__ = ("new_name",)

    new_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(f"RENAME TO {self.new_name}")


@dataclass
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


@dataclass
class RenameColumn(AlterColumnStatement):
    __slots__ = ("new_name",)

    new_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            f"RENAME COLUMN {self.column_name} TO {self.new_name}"
        )


@dataclass
class DropColumn(AlterColumnStatement):
    @property
    def querystring(self) -> QueryString:
        return QueryString(f"DROP COLUMN {self.column_name}")


@dataclass
class AddColumn(AlterColumnStatement):
    __slots__ = (
        "column",
        "name",
    )

    column: Column
    name: str

    @property
    def querystring(self) -> QueryString:
        self.column._meta.name = self.name
        return QueryString("ADD COLUMN {}", self.column.querystring)


@dataclass
class Unique(AlterColumnStatement):
    __slots__ = ("boolean",)

    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(f"ADD UNIQUE ({self.column_name})")
        else:
            if isinstance(self.column, str):
                raise ValueError(
                    "Removing a unique constraint requires a Column instance "
                    "to be passed as the column arg instead of a string."
                )
            tablename = self.column._meta.table._meta.tablename
            column_name = self.column_name
            key = f"{tablename}_{column_name}_key"
            return QueryString(f'DROP CONSTRAINT "{key}"')


@dataclass
class Null(AlterColumnStatement):
    __slots__ = ("boolean",)

    boolean: bool

    @property
    def querystring(self) -> QueryString:
        if self.boolean:
            return QueryString(
                "ALTER COLUMN {} DROP NOT NULL", self.column_name
            )
        else:
            return QueryString(
                "ALTER COLUMN {} SET NOT NULL", self.column_name
            )


@dataclass
class SetLength(AlterColumnStatement):

    __slots__ = ("length",)

    length: int

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            "ALTER COLUMN {} TYPE VARCHAR({})", self.column_name, self.length
        )


@dataclass
class DropConstraint(AlterStatement):
    __slots__ = ("constraint_name",)

    constraint_name: str

    @property
    def querystring(self) -> QueryString:
        return QueryString(
            "DROP CONSTRAINT IF EXISTS {}", self.constraint_name
        )


@dataclass
class AddForeignKeyConstraint(AlterStatement):
    __slots__ = (
        "constraint_name",
        "foreign_key_column_name",
        "referenced_table_name",
        "on_delete",
        "on_update",
    )

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


@dataclass
class SetDigits(AlterColumnStatement):

    __slots__ = ("digits", "column_type")

    digits: t.Optional[t.Tuple[int, int]]
    column_type: str

    @property
    def querystring(self) -> QueryString:
        if self.digits is not None:
            precision = self.digits[0]
            scale = self.digits[1]
            return QueryString(
                f"ALTER COLUMN {self.column_name} TYPE "
                f"{self.column_type}({precision}, {scale})"
            )
        else:
            return QueryString(
                f"ALTER COLUMN {self.column_name} TYPE {self.column_type}",
            )


class Alter(Query):

    __slots__ = (
        "_add_foreign_key_constraint",
        "_add",
        "_drop_contraint",
        "_drop_table",
        "_drop",
        "_null",
        "_rename_columns",
        "_rename_table",
        "_set_length",
        "_unique",
        "_set_digits",
    )

    def __init__(self, table: t.Type[Table]):
        super().__init__(table)
        self._add_foreign_key_constraint: t.List[AddForeignKeyConstraint] = []
        self._add: t.List[AddColumn] = []
        self._drop_contraint: t.List[DropConstraint] = []
        self._drop_table = False
        self._drop: t.List[DropColumn] = []
        self._null: t.List[Null] = []
        self._rename_columns: t.List[RenameColumn] = []
        self._rename_table: t.List[RenameTable] = []
        self._set_length: t.List[SetLength] = []
        self._unique: t.List[Unique] = []
        self._set_digits: t.List[SetDigits] = []

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

    def rename_table(self, new_name: str) -> Alter:
        """
        Band.alter().rename_table('musical_group')
        """
        # We override the existing one rather than appending.
        self._rename_table = [RenameTable(new_name=new_name)]
        return self

    def rename_column(
        self, column: t.Union[str, Column], new_name: str
    ) -> Alter:
        """
        Band.alter().rename_column(Band.popularity, ‘rating’)
        Band.alter().rename_column('popularity', ‘rating’)
        """
        self._rename_columns.append(RenameColumn(column, new_name))
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

    def set_length(self, column: t.Union[str, Varchar], length: int) -> Alter:
        """
        Change the max length of a varchar column. Unfortunately, this isn't
        supported by SQLite, but SQLite also doesn't enforce any length limits
        on varchar columns anyway.

        Band.alter().set_length('name', 512)
        """
        if self.engine_type == "sqlite":
            colored_warning(
                (
                    "SQLITE doesn't support changes in length. It also "
                    "doesn't enforce any length limits, so your code will "
                    "still work as expected. Skipping."
                ),
                level=Level.medium,
            )
            return self

        if not isinstance(column, (str, Varchar)):
            raise ValueError(
                "Only Varchar columns can have their length changed."
            )

        self._set_length.append(SetLength(column, length))
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

    def set_digits(
        self,
        column: t.Union[str, Numeric],
        digits: t.Optional[t.Tuple[int, int]],
    ) -> Alter:
        """
        Alter the precision and scale for a Numeric column.
        """
        column_type = (
            column.__class__.__name__.upper()
            if isinstance(column, Numeric)
            else "NUMERIC"
        )
        self._set_digits.append(
            SetDigits(digits=digits, column=column, column_type=column_type,)
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
                            (
                                f"UPDATE {tablename} "
                                f"SET {column._meta.name} = "
                                "{} WHERE id = {}"
                            ),
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
                self._add,
                self._rename_columns,
                self._rename_table,
                self._drop,
                self._unique,
                self._null,
                self._set_length,
                self._set_digits,
            )
        ]

        if self.engine_type == "sqlite":
            # Can only perform one alter statement at a time.
            query += " {}"
            return [QueryString(query, i) for i in alterations]

        # Postgres can perform them all at once:
        query += ",".join([" {}" for i in alterations])

        return [QueryString(query, *alterations)]
