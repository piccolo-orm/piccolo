from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import typing as t

from piccolo.columns.operators.comparison import (
    ComparisonOperator,
    Equal,
    GreaterEqualThan,
    GreaterThan,
    ILike,
    In,
    IsNull,
    LessEqualThan,
    LessThan,
    Like,
    NotEqual,
    NotIn,
    NotLike,
)
from piccolo.columns.combination import Where
from piccolo.custom_types import Iterable
from piccolo.querystring import QueryString
from piccolo.utils.warnings import colored_warning

if t.TYPE_CHECKING:
    from piccolo.table import Table  # noqa
    from .column_types import ForeignKey  # noqa


class OnDelete(str, Enum):
    cascade = "CASCADE"
    restrict = "RESTRICT"
    no_action = "NO ACTION"
    set_null = "SET NULL"
    set_default = "SET DEFAULT"


class OnUpdate(str, Enum):
    cascade = "CASCADE"
    restrict = "RESTRICT"
    no_action = "NO ACTION"
    set_null = "SET NULL"
    set_default = "SET DEFAULT"


@dataclass
class ForeignKeyMeta:
    references: t.Type[Table]
    on_delete: OnDelete
    on_update: OnUpdate
    proxy_columns: t.List[Column] = field(default_factory=list)


@dataclass
class ColumnMeta:
    """
    We store as many attributes in ColumnMeta as possible, to help avoid name
    clashes with user defined attributes.
    """

    # General attributes:
    null: bool = False
    primary: bool = False
    key: bool = False
    unique: bool = False
    index: bool = False

    # Used for representing the table in migrations and the playground.
    params: t.Dict[str, t.Any] = field(default_factory=dict)

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None
    _table: t.Optional[t.Type[Table]] = None

    # Used by Foreign Keys:
    call_chain: t.List["ForeignKey"] = field(default_factory=lambda: [])
    table_alias: t.Optional[str] = None

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "`_name` isn't defined - the Table Metaclass should set it."
            )
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def table(self) -> t.Type[Table]:
        if not self._table:
            raise ValueError(
                "`_table` isn't defined - the Table Metaclass should set it."
            )
        return self._table

    @property
    def engine_type(self) -> str:
        engine = self.table._meta.db
        if engine:
            return engine.engine_type
        else:
            raise ValueError("The table has no engine defined.")

    def get_full_name(self, just_alias=False) -> str:
        """
        Returns the full column name, taking into account joins.
        """
        column_name = self.name

        if not self.call_chain:
            return f"{self.table._meta.tablename}.{column_name}"

        column_name = (
            "$".join([i._meta.name for i in self.call_chain])
            + f"${column_name}"
        )
        alias = f"{self.call_chain[-1]._meta.table_alias}.{self.name}"
        if just_alias:
            return alias
        else:
            return f'{alias} AS "{column_name}"'


class Selectable(metaclass=ABCMeta):
    @abstractmethod
    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        """
        In a query, what to output after the select statement - could be a
        column name, a sub query, a function etc. For a column it will be the
        column name.
        """
        pass


class Column(Selectable):

    value_type: t.Type = int

    def __init__(
        self,
        null: bool = False,
        primary: bool = False,
        key: bool = False,
        unique: bool = False,
        index: bool = False,
        **kwargs,
    ) -> None:
        # Used for migrations:
        kwargs.update(
            {
                "null": null,
                "primary": primary,
                "key": key,
                "unique": unique,
                "index": index,
            }
        )

        self._meta = ColumnMeta(
            null=null,
            primary=primary,
            key=key,
            unique=unique,
            index=index,
            params=kwargs,
        )

    def is_in(self, values: Iterable) -> Where:
        return Where(column=self, values=values, operator=In)

    def not_in(self, values: Iterable) -> Where:
        return Where(column=self, values=values, operator=NotIn)

    def like(self, value: str) -> Where:
        if "%" not in value:
            raise ValueError("% is required for like operators")
        return Where(column=self, value=value, operator=Like)

    def ilike(self, value: str) -> Where:
        if "%" not in value:
            raise ValueError("% is required for ilike operators")
        if self._meta.engine_type == "postgres":
            operator: t.Type[ComparisonOperator] = ILike
        else:
            colored_warning(
                "SQLite doesn't support ILIKE currently, falling back to LIKE."
            )
            operator = Like
        return Where(column=self, value=value, operator=operator)

    def not_like(self, value: str) -> Where:
        if "%" not in value:
            raise ValueError("% is required for like operators")
        return Where(column=self, value=value, operator=NotLike)

    def __lt__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessThan)

    def __le__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessEqualThan)

    def __gt__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterThan)

    def __ge__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterEqualThan)

    def __eq__(self, value) -> Where:  # type: ignore
        if value is None:
            return Where(column=self, operator=IsNull)
        else:
            return Where(column=self, value=value, operator=Equal)

    def __ne__(self, value) -> Where:  # type: ignore
        return Where(column=self, value=value, operator=NotEqual)

    def __hash__(self):
        return hash(self._meta.name)

    def get_default_value(self) -> t.Any:
        """
        If the column has a default attribute, return it. If it's callable,
        return the response instead.
        """
        default = getattr(self, "default", None)
        if default is not None:
            default = default.value if isinstance(default, Enum) else default
            # Can't use inspect - can't tell that datetime.datetime.now
            # is a callable.
            is_callable = hasattr(default, "__call__")
            value = default() if is_callable else default
            return value
        return None

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        """
        How to refer to this column in a SQL query.
        """
        return self._meta.get_full_name(just_alias=just_alias)

    @property
    def querystring(self) -> QueryString:
        """
        Used when creating tables.
        """
        column_type = getattr(
            self, "column_type", self.__class__.__name__.upper()
        )
        query = f'"{self._meta.name}" {column_type}'
        if self._meta.primary:
            query += " PRIMARY"
        if self._meta.key:
            query += " KEY"
        if self._meta.unique:
            query += " UNIQUE"
        if not self._meta.null:
            query += " NOT NULL"

        foreign_key_meta: t.Optional[ForeignKeyMeta] = getattr(
            self, "_foreign_key_meta", None
        )
        if foreign_key_meta:
            tablename = foreign_key_meta.references._meta.tablename
            on_delete = foreign_key_meta.on_delete.value
            on_update = foreign_key_meta.on_update.value
            query += (
                f" REFERENCES {tablename} (id) "
                f"ON DELETE {on_delete} "
                f"ON UPDATE {on_update}"
            )

        return QueryString(query)

    def __str__(self):
        return self.querystring.__str__()

    def __repr__(self):
        return f"{self._meta.name} - {self.__class__.__name__}"
