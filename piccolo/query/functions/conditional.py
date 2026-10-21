from __future__ import annotations

import datetime
import decimal
import uuid
from typing import TYPE_CHECKING, Any, Optional, Union

from piccolo.custom_types import BasicTypes, Combinable
from piccolo.querystring import QueryString

if TYPE_CHECKING:
    from piccolo.columns import Column
    from piccolo.table import Table


class Coalesce(QueryString):
    def __init__(
        self,
        *args: Union[Column, QueryString, BasicTypes],
        alias: Optional[str] = None,
    ):
        """
        Returns the first non-null value.

        Here's an example to try in the playground::

            >>> await Album.select(Album.release_date)
            [
                {'release_date': datetime.date(2021, 1, 1)},
                {'release_date': datetime.date(2025, 1, 1)},
                {'release_date': datetime.date(2022, 2, 2)},
                {'release_date': None}
            ]

        One of the values is null - we can specify a fallback value::

            >>> from piccolo.functions.conditional import Coalesce
            >>> await Album.select(
            ...     Coalesce(Album.release_date, datetime.date(2050, 1, 1))
            ... )
            [
                {'release_date': datetime.date(2021, 1, 1)},
                {'release_date': datetime.date(2025, 1, 1)},
                {'release_date': datetime.date(2022, 2, 2)},
                {'release_date': datetime.date(2050, 1, 1)}
            ]

        Or us this abbreviated syntax::

            >>> await Album.select(
            ...     Album.release_date | datetime.date(2050, 1, 1)
            ... )
            [
                {'release_date': datetime.date(2021, 1, 1)},
                {'release_date': datetime.date(2025, 1, 1)},
                {'release_date': datetime.date(2022, 2, 2)},
                {'release_date': datetime.date(2050, 1, 1)}
            ]

        """
        if len(args) < 2:
            raise ValueError("At least two values must be passed in.")

        #######################################################################
        # Preserve the original alias from the column.

        from piccolo.columns import Column

        first_arg = args[0]

        if isinstance(first_arg, Column):
            alias = (
                alias
                or first_arg._alias
                or first_arg._meta.get_default_alias()
            )
        elif isinstance(first_arg, QueryString):
            alias = alias or first_arg._alias

        #######################################################################

        placeholders = ", ".join("{}" for _ in args)

        super().__init__(f"COALESCE({placeholders})", *args, alias=alias)


class NullIf(QueryString):
    def __init__(
        self,
        identifier: Union[Column, QueryString],
        value: Union[BasicTypes, QueryString],
        alias: Optional[str] = None,
    ):
        """
        Returns null if the value in the database equals ``value``.

        An example is where a ``Varchar`` or ``Text`` column contains a mix of
        empty strings and null. We might want to standardise the response so
        it's just null.

        For example::

            class Venue(Table):
                name = Varchar()
                address = Text(null=True)

            >>> await Venue.select(Venue.name, NullIf(Venue.address, ''))
            [{'name': 'Amazing venue', 'address': None}]

        """
        # Preserve the original alias from the column.

        from piccolo.columns import Column

        if isinstance(identifier, Column):
            alias = (
                alias
                or identifier._alias
                or identifier._meta.get_default_alias()
            )
        elif isinstance(identifier, QueryString):
            alias = alias or identifier._alias

        #######################################################################

        super().__init__("NULLIF({}, {})", identifier, value, alias=alias)


###############################################################################


def get_cast_column(value: Any) -> Optional[Column]:
    """
    Works out which column type a plain Python value should be cast to.

    :returns:
        ``None`` if we don't know how to cast the value.

    """
    from piccolo.columns import column_types

    if isinstance(value, datetime.datetime):
        return (
            column_types.Timestamptz()
            if value.tzinfo
            else column_types.Timestamp()
        )

    # bool first - it's a subclass of int.
    for py_type, column_class in (
        (bool, column_types.Boolean),
        (int, column_types.BigInt),
        (float, column_types.DoublePrecision),
        (decimal.Decimal, column_types.Numeric),
        (str, column_types.Text),
        (datetime.date, column_types.Date),
        (datetime.time, column_types.Time),
        (datetime.timedelta, column_types.Interval),
        (uuid.UUID, column_types.UUID),
        (bytes, column_types.Bytea),
    ):
        if isinstance(value, py_type):
            return column_class()

    return None


def get_case_value(
    value: Union[Column, QueryString, BasicTypes, None],
    table: Optional[type[Table]] = None,
) -> Any:
    """
    Works out how a ``THEN`` / ``ELSE`` value should appear in the SQL.

    With Postgres and Cockroach, plain Python values are wrapped in a
    ``CAST``, because the database can't infer the type of a bare parameter
    inside a ``CASE`` statement (Postgres assumes ``text``, Cockroach raises
    ``IndeterminateDatatypeError``)::

        CASE WHEN "band"."popularity" > $1 THEN CAST($2 AS TEXT) END

    SQLite doesn't need the ``CAST`` - and casting a date string to ``DATE``
    in SQLite actually corrupts it (``'2021-01-01'`` becomes ``2021``).

    Columns and other functions are inserted as they are.

    :param table:
        Used to work out which database engine is being used. If not
        specified, the default engine is used.

    """
    from piccolo.columns import Column
    from piccolo.query.functions.type_conversion import Cast
    from piccolo.table import create_table_class

    if value is None:
        return QueryString("NULL")

    if isinstance(value, (Column, QueryString)):
        return value

    # The column type is sometimes dependent on which database is being
    # used, so the column needs a reference to a table.
    table = table or create_table_class("Table")

    if table._meta.db.engine_type == "sqlite":
        return value

    cast_column = get_cast_column(value)
    if cast_column is None:
        return value

    cast_column._meta.table = table
    return Cast(value, cast_column)


class When(QueryString):
    def __init__(
        self,
        condition: Union[Combinable, QueryString],
        then: Union[Column, QueryString, BasicTypes, None],
    ):
        """
        A single branch of a :class:`Case` statement - don't use it directly.

        :param condition:
            A where clause, for example ``Band.popularity > 1000``.
        :param then:
            The value to return if the condition is true.

        """
        from piccolo.columns.combination import Combination, Where, WhereRaw

        if isinstance(condition, (Where, WhereRaw, Combination)):
            condition = condition.querystring
        elif not isinstance(condition, QueryString):
            raise ValueError("The condition must be a where clause.")

        table = condition.columns[0]._meta.table if condition.columns else None

        super().__init__(
            "WHEN {} THEN {}",
            condition,
            get_case_value(then, table=table),
        )


class Case(QueryString):
    def __init__(
        self,
        *when_conditions: When,
        default: Union[Column, QueryString, BasicTypes, None] = None,
        alias: Optional[str] = None,
    ):
        """
        A SQL ``CASE`` statement - it returns a different value depending on
        which condition is matched first. It's the SQL equivalent of an
        ``if / elif / else`` block.

        Here's an example to try in the playground::

            >>> from piccolo.query.functions import Case, When

            >>> await Band.select(
            ...     Band.name,
            ...     Case(
            ...         When(Band.popularity > 900, then='super popular'),
            ...         When(Band.popularity > 500, then='popular'),
            ...         default='not popular',
            ...         alias='popularity_label',
            ...     ),
            ... )
            [
                {'name': 'Pythonistas', 'popularity_label': 'super popular'},
                {'name': 'Rustaceans', 'popularity_label': 'not popular'},
                {'name': 'C-Sharps', 'popularity_label': 'popular'}
            ]

        It can also be used in a ``where`` clause, and to sort results::

            >>> await Band.select(Band.name).order_by(
            ...     Case(
            ...         When(Band.name == 'Rustaceans', then=1),
            ...         default=2,
            ...     )
            ... )

        :param when_conditions:
            Each branch of the statement, which are evaluated in order.
        :param default:
            The value to return if none of the conditions match (``ELSE`` in
            SQL). If not specified, ``null`` is returned.
        :param alias:
            The name of the column in the response.

        """
        if not when_conditions:
            raise ValueError("At least one `When` must be passed in.")

        if not all(isinstance(when, When) for when in when_conditions):
            raise ValueError("Only `When` instances can be passed in.")

        template = " ".join("{}" for _ in when_conditions)
        args: list[Any] = list(when_conditions)

        if default is not None:
            table = next(
                (
                    when.columns[0]._meta.table
                    for when in when_conditions
                    if when.columns
                ),
                None,
            )
            template += " ELSE {}"
            args.append(get_case_value(default, table=table))

        super().__init__(
            f"CASE {template} END",
            *args,
            alias=alias or "case",
        )
