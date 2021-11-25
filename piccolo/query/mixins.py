from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from piccolo.columns import And, Column, Or, Where
from piccolo.columns.column_types import ForeignKey
from piccolo.custom_types import Combinable
from piccolo.querystring import QueryString
from piccolo.utils.sql_values import convert_to_sql_value

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Selectable
    from piccolo.table import Table  # noqa


@dataclass
class Limit:
    __slots__ = ("number",)

    number: int

    def __post_init__(self):
        if type(self.number) != int:
            raise TypeError("Limit must be an integer")

    @property
    def querystring(self) -> QueryString:
        return QueryString(f" LIMIT {self.number}")

    def __str__(self) -> str:
        return self.querystring.__str__()

    def copy(self) -> Limit:
        return self.__class__(number=self.number)


@dataclass
class Offset:
    __slots__ = ("number",)

    number: int

    def __post_init__(self):
        if type(self.number) != int:
            raise TypeError("Limit must be an integer")

    @property
    def querystring(self) -> QueryString:
        return QueryString(f" OFFSET {self.number}")

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class OrderBy:
    __slots__ = ("columns", "ascending")

    columns: t.Sequence[Column]
    ascending: bool

    @property
    def querystring(self) -> QueryString:
        order = "ASC" if self.ascending else "DESC"
        columns_names = ", ".join(
            i._meta.get_full_name(just_alias=True) for i in self.columns
        )

        return QueryString(f" ORDER BY {columns_names} {order}")

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class Output:

    as_json: bool = False
    as_list: bool = False
    as_objects: bool = False
    load_json: bool = False
    nested: bool = False

    def copy(self) -> Output:
        return self.__class__(
            as_json=self.as_json,
            as_list=self.as_list,
            as_objects=self.as_objects,
            load_json=self.load_json,
            nested=self.nested,
        )


@dataclass
class WhereDelegate:

    _where: t.Optional[Combinable] = None
    _where_columns: t.List[Column] = field(default_factory=list)

    def get_where_columns(self):
        """
        Retrieves all columns used in the where clause - in case joins are
        needed.
        """
        self._where_columns = []
        self._extract_columns(self._where)
        return self._where_columns

    def _extract_columns(self, combinable: Combinable):
        if isinstance(combinable, Where):
            self._where_columns.append(combinable.column)
        elif isinstance(combinable, (And, Or)):
            self._extract_columns(combinable.first)
            self._extract_columns(combinable.second)

    def where(self, *where: Combinable):
        for arg in where:
            self._where = And(self._where, arg) if self._where else arg


@dataclass
class OrderByDelegate:

    _order_by: t.Optional[OrderBy] = None

    def get_order_by_columns(self) -> t.List[Column]:
        return list(self._order_by.columns) if self._order_by else []

    def order_by(self, *columns: Column, ascending=True):
        self._order_by = OrderBy(columns, ascending)


@dataclass
class LimitDelegate:

    _limit: t.Optional[Limit] = None
    _first: bool = False

    def limit(self, number: int):
        self._limit = Limit(number)

    def first(self):
        self.limit(1)
        self._first = True

    def copy(self) -> LimitDelegate:
        _limit = self._limit.copy() if self._limit is not None else None
        return self.__class__(_limit=_limit, _first=self._first)


@dataclass
class DistinctDelegate:

    _distinct: bool = False

    def distinct(self):
        self._distinct = True


@dataclass
class CountDelegate:

    _count: bool = False

    def count(self):
        self._count = True


@dataclass
class AddDelegate:

    _add: t.List[Table] = field(default_factory=list)

    def add(self, *instances: Table, table_class: t.Type[Table]):
        for instance in instances:
            if not isinstance(instance, table_class):
                raise TypeError("Incompatible type added.")

        self._add += instances


@dataclass
class OutputDelegate:
    """
    Example usage:

    .output(as_list=True)
    .output(as_json=True)
    .output(as_json=True, as_list=True)
    """

    _output: Output = field(default_factory=Output)

    def output(
        self,
        as_list: t.Optional[bool] = None,
        as_json: t.Optional[bool] = None,
        load_json: t.Optional[bool] = None,
        nested: t.Optional[bool] = None,
    ):
        """
        :param as_list:
            If each row only returns a single value, compile all of the results
            into a single list.
        :param as_json:
            The results are serialised into JSON. It's equivalent to running
            `json.dumps` on the result.
        :param load_json:
            If True, any JSON fields will have the JSON values returned from
            the database loaded as Python objects.
        """
        # We do it like this, so output can be called multiple times, without
        # overriding any existing values if they're not specified.
        if as_list is not None:
            self._output.as_list = bool(as_list)

        if as_json is not None:
            self._output.as_json = bool(as_json)

        if load_json is not None:
            self._output.load_json = bool(load_json)

        if nested is not None:
            self._output.nested = bool(nested)

    def copy(self) -> OutputDelegate:
        _output = self._output.copy() if self._output is not None else None
        return self.__class__(_output=_output)


@dataclass
class PrefetchDelegate:
    """
    Example usage:

    .prefetch(MyTable.column_a, MyTable.column_b)
    """

    fk_columns: t.List[ForeignKey] = field(default_factory=list)

    def prefetch(self, *fk_columns: t.Union[ForeignKey, t.List[ForeignKey]]):
        """
        :param columns:
            We accept ``ForeignKey`` and ``List[ForeignKey]`` here, in case
            someone passes in a list by accident when using ``all_related()``,
            in which case we flatten the list.

        """
        _fk_columns: t.List[ForeignKey] = []
        for column in fk_columns:
            if isinstance(column, list):
                _fk_columns.extend(column)
            else:
                _fk_columns.append(column)

        combined = self.fk_columns + _fk_columns
        self.fk_columns = combined


@dataclass
class ColumnsDelegate:
    """
    Example usage:

    .columns(MyTable.column_a, MyTable.column_b)
    """

    selected_columns: t.Sequence[Selectable] = field(default_factory=list)

    def columns(self, *columns: t.Union[Selectable, t.List[Selectable]]):
        """
        :param columns:
            We accept ``Selectable`` and ``List[Selectable]`` here, in case
            someone passes in a list by accident when using ``all_columns()``,
            in which case we flatten the list.

        """
        _columns = []
        for column in columns:
            if isinstance(column, list):
                _columns.extend(column)
            else:
                _columns.append(column)

        combined = list(self.selected_columns) + _columns
        self.selected_columns = combined

    def remove_secret_columns(self):
        non_secret = []
        for i in self.selected_columns:
            if isinstance(i, Column) and i._meta.secret:
                continue
            non_secret.append(i)
        self.selected_columns = non_secret


@dataclass
class ValuesDelegate:
    """
    Used to specify new column values - primarily used in update queries.
    """

    table: t.Type[Table]
    _values: t.Dict[Column, t.Any] = field(default_factory=dict)

    def values(self, values: t.Dict[t.Union[Column, str], t.Any]):
        """
        Example usage:

        .. code-block:: python

            .values({MyTable.column_a: 1})

            # Or:
            .values({'column_a': 1})

            # Or:
            .values(column_a=1})

        """
        cleaned_values: t.Dict[Column, t.Any] = {}
        for key, value in values.items():
            if isinstance(key, Column):
                column = key
            elif isinstance(key, str):
                column = self.table._meta.get_column_by_name(key)
            else:
                raise ValueError(
                    f"Unrecognised key - {key} is neither a Column or the "
                    "name of a Column."
                )
            cleaned_values[column] = value

        self._values.update(cleaned_values)

    def get_sql_values(self) -> t.List[t.Any]:
        """
        Convert any Enums into values, and serialise any JSON.
        """
        return [
            convert_to_sql_value(value=value, column=column)
            for column, value in self._values.items()
        ]


@dataclass
class OffsetDelegate:
    """
    Used to offset the results - for example, to return row 100 and onward.

    Typically used in conjunction with order_by and limit.

    Example usage:

    .offset(100)
    """

    _offset: t.Optional[Offset] = None

    def offset(self, number: int = 0):
        self._offset = Offset(number)


@dataclass
class GroupBy:
    __slots__ = ("columns",)

    columns: t.Sequence[Column]

    @property
    def querystring(self) -> QueryString:
        columns_names = ", ".join(
            i._meta.get_full_name(just_alias=True) for i in self.columns
        )

        return QueryString(f" GROUP BY {columns_names}")

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class GroupByDelegate:
    """
    Used to group results - needed when doing aggregation.

    .group_by(Band.name)
    """

    _group_by: t.Optional[GroupBy] = None

    def group_by(self, *columns: Column):
        self._group_by = GroupBy(columns=columns)
