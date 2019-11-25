from __future__ import annotations
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
import typing as t

from piccolo.columns.operators import (
    Equal,
    GreaterEqualThan,
    GreaterThan,
    In,
    LessEqualThan,
    LessThan,
    Like,
    ILike,
    NotEqual,
    NotIn,
    NotLike,
    Operator,
)
from piccolo.columns.combination import Where
from piccolo.custom_types import Iterable
from piccolo.querystring import QueryString
from piccolo.utils.warnings import colored_warning

if t.TYPE_CHECKING:
    from piccolo.table import Table  # noqa
    from .column_types import ForeignKey  # noqa


@dataclass
class ColumnMeta:
    """
    We store as many attributes in ColumnMeta as possible, to help avoid name
    clashes with user defined attributes.
    """

    # General attributes:
    null: bool = True
    primary: bool = False
    key: bool = False
    unique: bool = False

    # Used for representing the table in migrations and the playground.
    params: t.Dict[str, t.Any] = field(default_factory=dict)

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None
    _table: t.Optional[Table] = None

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
    def table(self) -> Table:
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
        null: bool = True,
        primary: bool = False,
        key: bool = False,
        unique: bool = False,
        **kwargs,
    ) -> None:
        # Used for migrations:
        kwargs.update(
            {"null": null, "primary": primary, "key": key, "unique": unique}
        )

        self._meta = ColumnMeta(
            null=null, primary=primary, key=key, unique=unique, params=kwargs
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
            operator: t.Type[Operator] = ILike
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
        return Where(column=self, value=value, operator=Equal)

    def __ne__(self, value) -> Where:  # type: ignore
        return Where(column=self, value=value, operator=NotEqual)

    def __hash__(self):
        return hash(self._meta.name)

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
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

        foreign_key_meta = getattr(self, "_foreign_key_meta", None)
        if foreign_key_meta:
            references = foreign_key_meta.references
            query += f" REFERENCES {references._meta.tablename}"

        return QueryString(query)

    def __str__(self):
        return self.querystring.__str__()
