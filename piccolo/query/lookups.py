"""
Lookup parsing for :meth:`Table.filter <piccolo.table.Table.filter>` and
:meth:`Table.criteria <piccolo.table.Table.criteria>`.

A lookup is a string of the form
``field[__related_field...][__transform][__op]`` which is parsed into a where
clause:

.. code-block:: python

    "name"                 -> Band.name == value
    "popularity__gte"      -> Band.popularity >= value
    "manager__name__in"    -> Band.manager.name.is_in(value)
    "starts__year__gte"    -> Year(Concert.starts) >= value

"""

from __future__ import annotations

from operator import eq, ge, gt, le, lt
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional

from piccolo.columns.base import Column
from piccolo.columns.column_types import Date, Time, Timestamp, Timestamptz
from piccolo.columns.combination import WhereRaw
from piccolo.query.functions.datetime import (
    Day,
    Hour,
    Minute,
    Month,
    Second,
    Year,
)
from piccolo.querystring import QueryString

if TYPE_CHECKING:
    from piccolo.custom_types import Combinable
    from piccolo.table import Table


class Transform(NamedTuple):
    function: Callable[[Any], QueryString]
    column_types: tuple[type[Column], ...]


DATE_COLUMNS = (Date, Timestamp, Timestamptz)
TIME_COLUMNS = (Time, Timestamp, Timestamptz)

LOOKUP_TRANSFORMS: dict[str, Transform] = {
    "year": Transform(Year, DATE_COLUMNS),
    "month": Transform(Month, DATE_COLUMNS),
    "day": Transform(Day, DATE_COLUMNS),
    "hour": Transform(Hour, TIME_COLUMNS),
    "minute": Transform(Minute, TIME_COLUMNS),
    "second": Transform(Second, TIME_COLUMNS),
}


def _is_in(expression: Any, value: Any) -> Any:
    """
    ``Column.is_in`` expands the values into one placeholder each, but
    ``QueryString.is_in`` binds the whole list as a single parameter, which
    isn't valid SQL. Transforms give us a ``QueryString``, so that case is
    built here instead.
    """
    from piccolo.query.methods.select import Select

    if isinstance(value, (str, bytes)):
        raise ValueError(
            "An `in` lookup needs a sequence of values, not a string."
        )

    values: Any
    if isinstance(value, (Select, QueryString)):
        values = value
    else:
        # Normalise tuples, sets and other iterables - `Column.is_in` only
        # rejects an empty `list`, and `IN ()` isn't valid SQL.
        values = list(value)
        if not values:
            raise ValueError(
                "The `values` list argument must contain at least one value."
            )

    if not isinstance(expression, QueryString):
        return expression.is_in(values)

    if isinstance(values, Select):
        if len(values.columns_delegate.selected_columns) != 1:
            raise ValueError("A sub select must only return a single column.")
        values = values.querystrings[0]

    if isinstance(values, QueryString):
        return QueryString("{} IN ({})", expression, values)

    placeholders = ", ".join("{}" for _ in values)
    return QueryString(f"{{}} IN ({placeholders})", expression, *values)


LOOKUP_OPERATORS: dict[str, Callable[[Any, Any], Any]] = {
    "gte": ge,
    "lte": le,
    "gt": gt,
    "lt": lt,
    "in": _is_in,
}


def build_expression(
    table: type[Table], lookup: str, value: Any
) -> Combinable:
    """
    Turn a single ``lookup`` string and its ``value`` into a where clause
    against ``table``.
    """
    tokens = lookup.split("__")

    # A column always wins over a suffix which happens to share its name -
    # `Event.year` beats the `year` transform, and a related `lt` column beats
    # the `lt` operator - so a suffix is only stripped once the lookup has
    # failed to resolve as it stands.
    column = _find_column(table, tokens)
    operator = eq
    transform: Optional[Transform] = None

    if column is None and len(tokens) > 1 and tokens[-1] in LOOKUP_OPERATORS:
        operator = LOOKUP_OPERATORS[tokens.pop()]
        column = _find_column(table, tokens)

    if column is None and len(tokens) > 1 and tokens[-1] in LOOKUP_TRANSFORMS:
        transform = LOOKUP_TRANSFORMS[tokens.pop()]
        column = _find_column(table, tokens)

    if column is None:
        raise ValueError(f"Invalid lookup - {lookup}")

    if transform is None:
        return _as_combinable(operator(column, value), column)

    if not isinstance(column, transform.column_types):
        raise ValueError(
            f"Invalid lookup - {lookup} - a transform needs a date or time "
            f"column, and {column._meta.name} is {type(column).__name__}."
        )

    return _as_combinable(operator(transform.function(column), value), column)


def _find_column(table: type[Table], tokens: list[str]) -> Optional[Column]:
    """
    The column the lookup points at, or ``None`` if there isn't one.

    ``get_column_by_name`` walks the path with ``getattr``, so a lookup like
    ``name__like`` resolves to a *method* on the column - hence the type
    check, otherwise it would be compared against the value.

    Anything the walk raises means "not a column": as well as ``ValueError``,
    an over-long path through a self-referencing foreign key raises a bare
    ``Exception`` from ``ForeignKey.__getattribute__``.
    """
    try:
        column = table._meta.get_column_by_name(".".join(tokens))
    except Exception:
        return None

    return column if isinstance(column, Column) else None


def _as_combinable(clause: Any, column: Column) -> Combinable:
    """
    Transforms return a ``QueryString`` rather than a ``Combinable``.
    ``WhereDelegate.where`` normalises those the same way when they're passed
    to ``where`` - we have to do it here too, so that ``|`` on the result
    means ``OR``. On a ``QueryString`` it means ``COALESCE``.
    """
    if not isinstance(clause, QueryString):
        return clause

    if column._meta.call_chain:
        return JoinedWhereRaw(column, clause.template, *clause.args)

    return WhereRaw(clause.template, *clause.args)


class JoinedWhereRaw(WhereRaw):
    """
    A ``WhereRaw`` which references a joined table.

    ``update`` and ``delete`` can't join, so ``Where`` rewrites a clause on a
    related column into a sub select. ``WhereRaw`` has no way of knowing it
    needs to - it just returns its SQL, which then names a table that isn't in
    the query - so the rewrite is repeated here.
    """

    __slots__ = ("column",)

    def __init__(self, column: Column, sql: str, *args: Any) -> None:
        super().__init__(sql, *args)
        self.column = column

    @property
    def querystring_for_update_and_delete(self) -> QueryString:
        root_column = self.column._meta.call_chain[0]
        sub_query = root_column._meta.table.select(root_column).where(self)

        return QueryString(
            f'"{root_column._meta.db_column_name}" IN ({{}})',
            sub_query.querystrings[0],
        )
