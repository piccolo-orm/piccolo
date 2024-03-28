from __future__ import annotations

import asyncio
import collections.abc
import itertools
import typing as t
from dataclasses import dataclass, field
from enum import Enum, auto

from piccolo.columns import And, Column, Or, Where
from piccolo.columns.column_types import ForeignKey
from piccolo.custom_types import Combinable
from piccolo.querystring import QueryString
from piccolo.utils.list import flatten
from piccolo.utils.sql_values import convert_to_sql_value

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Selectable
    from piccolo.table import Table  # noqa


class DistinctOnError(ValueError):
    """
    Raised when ``DISTINCT ON`` queries are malformed.
    """

    pass


@dataclass
class Distinct:
    __slots__ = ("enabled", "on")

    enabled: bool
    on: t.Optional[t.Sequence[Column]]

    @property
    def querystring(self) -> QueryString:
        if self.enabled:
            if self.on:
                column_names = ", ".join(
                    i._meta.get_full_name(with_alias=False) for i in self.on
                )
                return QueryString(f" DISTINCT ON ({column_names})")
            else:
                return QueryString(" DISTINCT")
        else:
            return QueryString(" ALL")

    def validate_on(self, order_by: OrderBy):
        """
        When using the `on` argument, the first column must match the first
        order by column.

        :raises DistinctOnError:
            If the columns don't match.

        """
        validated = True

        try:
            first_order_column = order_by.order_by_items[0].columns[0]
        except IndexError:
            validated = False
        else:
            if not self.on:
                validated = False
            elif isinstance(first_order_column, Column) and not self.on[
                0
            ]._equals(first_order_column):
                validated = False

        if not validated:
            raise DistinctOnError(
                "The first `order_by` column must match the first column "
                "passed to `on`."
            )

    def __str__(self) -> str:
        return self.querystring.__str__()

    def copy(self) -> Distinct:
        return self.__class__(enabled=self.enabled, on=self.on)


@dataclass
class Limit:
    __slots__ = ("number",)

    number: int

    def __post_init__(self):
        if not isinstance(self.number, int):
            raise TypeError("Limit must be an integer")

    @property
    def querystring(self) -> QueryString:
        return QueryString(f" LIMIT {self.number}")

    def __str__(self) -> str:
        return self.querystring.__str__()

    def copy(self) -> Limit:
        return self.__class__(number=self.number)


@dataclass
class AsOf:
    __slots__ = ("interval",)

    interval: str

    def __post_init__(self):
        if not isinstance(self.interval, str):
            raise TypeError("As Of must be a string. Example: '-1s'")

    @property
    def querystring(self) -> QueryString:
        return QueryString(f" AS OF SYSTEM TIME '{self.interval}'")

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class Offset:
    __slots__ = ("number",)

    number: int

    def __post_init__(self):
        if not isinstance(self.number, int):
            raise TypeError("Offset must be an integer")

    @property
    def querystring(self) -> QueryString:
        return QueryString(f" OFFSET {self.number}")

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class OrderByRaw:
    __slots__ = ("sql",)

    sql: str


@dataclass
class OrderByItem:
    __slots__ = ("columns", "ascending")

    columns: t.Sequence[t.Union[Column, OrderByRaw]]
    ascending: bool


@dataclass
class OrderBy:
    order_by_items: t.List[OrderByItem] = field(default_factory=list)

    @property
    def querystring(self) -> QueryString:
        order_by_strings: t.List[str] = []
        for order_by_item in self.order_by_items:
            order = "ASC" if order_by_item.ascending else "DESC"
            for column in order_by_item.columns:
                if isinstance(column, Column):
                    expression = column._meta.get_full_name(with_alias=False)
                elif isinstance(column, OrderByRaw):
                    expression = column.sql
                else:
                    raise ValueError("Unrecognised order_by")

                order_by_strings.append(f"{expression} {order}")

        return QueryString(f" ORDER BY {', '.join(order_by_strings)}")

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class Returning:
    __slots__ = ("columns",)

    columns: t.List[Column]

    @property
    def querystring(self) -> QueryString:
        column_names = []
        for column in self.columns:
            column_names.append(
                f'"{column._meta.db_column_name}" AS "{column._alias}"'
                if column._alias
                else f'"{column._meta.db_column_name}"'
            )

        columns_string = ", ".join(column_names)

        return QueryString(f" RETURNING {columns_string}")

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


class CallbackType(Enum):
    success = auto()


@dataclass
class Callback:
    kind: CallbackType
    target: t.Callable


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
            if isinstance(arg, bool):
                raise ValueError(
                    "A boolean value has been passed in to a where clause. "
                    "This is probably a mistake. For example "
                    "`.where(MyTable.some_column is None)` instead of "
                    "`.where(MyTable.some_column.is_null())`."
                )

            self._where = And(self._where, arg) if self._where else arg


@dataclass
class OrderByDelegate:

    _order_by: OrderBy = field(default_factory=OrderBy)

    def get_order_by_columns(self) -> t.List[Column]:
        """
        Used to work out which columns are needed for joins.
        """
        return [
            i
            for i in itertools.chain(
                *[i.columns for i in self._order_by.order_by_items]
            )
            if isinstance(i, Column)
        ]

    def order_by(self, *columns: t.Union[Column, OrderByRaw], ascending=True):
        if len(columns) < 1:
            raise ValueError("At least one column must be passed to order_by.")

        self._order_by.order_by_items.append(
            OrderByItem(columns=columns, ascending=ascending)
        )


@dataclass
class LimitDelegate:

    _limit: t.Optional[Limit] = None
    _first: bool = False

    def limit(self, number: int):
        self._limit = Limit(number)

    def copy(self) -> LimitDelegate:
        _limit = self._limit.copy() if self._limit is not None else None
        return self.__class__(_limit=_limit, _first=self._first)


@dataclass
class AsOfDelegate:
    """
    Time travel queries using "As Of" syntax.
    Currently supports Cockroach using AS OF SYSTEM TIME.
    """

    _as_of: t.Optional[AsOf] = None

    def as_of(self, interval: str = "-1s"):
        self._as_of = AsOf(interval)


@dataclass
class DistinctDelegate:

    _distinct: Distinct = field(
        default_factory=lambda: Distinct(enabled=False, on=None)
    )

    def distinct(
        self, enabled: bool, on: t.Optional[t.Sequence[Column]] = None
    ):
        if on and not isinstance(on, collections.abc.Sequence):
            # Check a sequence is passed in, otherwise the user will get some
            # unuseful errors later on.
            raise ValueError("`on` must be a sequence of `Column` instances")

        self._distinct = Distinct(enabled=enabled, on=on)


@dataclass
class ReturningDelegate:
    _returning: t.Optional[Returning] = None

    def returning(self, columns: t.Sequence[Column]):
        self._returning = Returning(columns=list(columns))


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
class CallbackDelegate:
    """
    Example usage:

    .callback(my_handler_function)
    .callback(print, on=CallbackType.success)
    .callback(my_handler_coroutine)
    .callback([handler1, handler2])
    """

    _callbacks: t.Dict[CallbackType, t.List[Callback]] = field(
        default_factory=lambda: {kind: [] for kind in CallbackType}
    )

    def callback(
        self,
        callbacks: t.Union[t.Callable, t.List[t.Callable]],
        *,
        on: CallbackType,
    ):
        if isinstance(callbacks, list):
            self._callbacks[on].extend(
                Callback(kind=on, target=callback) for callback in callbacks
            )
        else:
            self._callbacks[on].append(Callback(kind=on, target=callbacks))

    async def invoke(self, results: t.Any, *, kind: CallbackType) -> t.Any:
        """
        Utility function that invokes the registered callbacks in the correct
        way, handling both sync and async callbacks. Only callbacks of the
        given kind are invoked.
        Results are passed through the callbacks in the order they were added,
        with each callback able to transform them. This function returns the
        transformed results.
        """
        for callback in self._callbacks[kind]:
            if asyncio.iscoroutinefunction(callback.target):
                results = await callback.target(results)
            else:
                results = callback.target(results)

        return results


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
        _columns = flatten(columns)
        combined = list(self.selected_columns) + _columns
        self.selected_columns = combined

    def remove_secret_columns(self):
        non_secret = [
            i
            for i in self.selected_columns
            if not isinstance(i, Column) or not i._meta.secret
        ]

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

    Example usage::

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
            i._meta.get_full_name(with_alias=False) for i in self.columns
        )

        return QueryString(f" GROUP BY {columns_names}")

    def __str__(self):
        return self.querystring.__str__()


@dataclass
class GroupByDelegate:
    """
    Used to group results - needed when doing aggregation::

        .group_by(Band.name)

    """

    _group_by: t.Optional[GroupBy] = None

    def group_by(self, *columns: Column):
        self._group_by = GroupBy(columns=columns)


class OnConflictAction(str, Enum):
    """
    Specify which action to take on conflict.
    """

    do_nothing = "DO NOTHING"
    do_update = "DO UPDATE"


@dataclass
class OnConflictItem:
    target: t.Optional[t.Union[str, Column, t.Tuple[Column, ...]]] = None
    action: t.Optional[OnConflictAction] = None
    values: t.Optional[t.Sequence[t.Union[Column, t.Tuple[Column, t.Any]]]] = (
        None
    )
    where: t.Optional[Combinable] = None

    @property
    def target_string(self) -> str:
        target = self.target
        assert target

        def to_string(value) -> str:
            if isinstance(value, Column):
                return f'"{value._meta.db_column_name}"'
            else:
                raise ValueError("OnConflict.target isn't a valid type")

        if isinstance(target, str):
            return f'ON CONSTRAINT "{target}"'
        elif isinstance(target, Column):
            return f"({to_string(target)})"
        elif isinstance(target, tuple):
            columns_str = ", ".join([to_string(i) for i in target])
            return f"({columns_str})"
        else:
            raise ValueError("OnConflict.target isn't a valid type")

    @property
    def action_string(self) -> QueryString:
        action = self.action
        if isinstance(action, OnConflictAction):
            if action == OnConflictAction.do_nothing:
                return QueryString(OnConflictAction.do_nothing.value)
            elif action == OnConflictAction.do_update:
                values = []
                query = f"{OnConflictAction.do_update.value} SET"

                if not self.values:
                    raise ValueError("No values specified for `on conflict`")

                for value in self.values:
                    if isinstance(value, Column):
                        column_name = value._meta.db_column_name
                        query += f' "{column_name}"=EXCLUDED."{column_name}",'
                    elif isinstance(value, tuple):
                        column = value[0]
                        value_ = value[1]
                        if isinstance(column, Column):
                            column_name = column._meta.db_column_name
                        else:
                            raise ValueError("Unsupported column type")

                        query += f' "{column_name}"={{}},'
                        values.append(value_)

                return QueryString(query.rstrip(","), *values)

        raise ValueError("OnConflict.action isn't a valid type")

    @property
    def querystring(self) -> QueryString:
        query = " ON CONFLICT"
        values = []

        if self.target:
            query += f" {self.target_string}"

        if self.action:
            query += " {}"
            values.append(self.action_string)

        if self.where:
            query += " WHERE {}"
            values.append(self.where.querystring)

        return QueryString(query, *values)

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class OnConflict:
    """
    Multiple `ON CONFLICT` statements are allowed - which is why we have this
    parent class.
    """

    on_conflict_items: t.List[OnConflictItem] = field(default_factory=list)

    @property
    def querystring(self) -> QueryString:
        query = "".join("{}" for i in self.on_conflict_items)
        return QueryString(
            query, *[i.querystring for i in self.on_conflict_items]
        )

    def __str__(self) -> str:
        return self.querystring.__str__()


@dataclass
class OnConflictDelegate:
    """
    Used with insert queries to specify what to do when a query fails due to
    a constraint::

        .on_conflict(action='DO NOTHING')

        .on_conflict(action='DO UPDATE', values=[Band.popularity])

        .on_conflict(action='DO UPDATE', values=[(Band.popularity, 1)])

    """

    _on_conflict: OnConflict = field(default_factory=OnConflict)

    def on_conflict(
        self,
        target: t.Optional[t.Union[str, Column, t.Tuple[Column, ...]]] = None,
        action: t.Union[
            OnConflictAction, t.Literal["DO NOTHING", "DO UPDATE"]
        ] = OnConflictAction.do_nothing,
        values: t.Optional[
            t.Sequence[t.Union[Column, t.Tuple[Column, t.Any]]]
        ] = None,
        where: t.Optional[Combinable] = None,
    ):
        action_: OnConflictAction
        if isinstance(action, OnConflictAction):
            action_ = action
        elif isinstance(action, str):
            action_ = OnConflictAction(action.upper())
        else:
            raise ValueError("Unrecognised `on conflict` action.")

        if where and action_ == OnConflictAction.do_nothing:
            raise ValueError(
                "The `where` option can only be used with DO NOTHING."
            )

        self._on_conflict.on_conflict_items.append(
            OnConflictItem(
                target=target, action=action_, values=values, where=where
            )
        )
