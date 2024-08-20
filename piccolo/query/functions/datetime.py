import typing as t

from piccolo.columns.base import Column
from piccolo.columns.column_types import (
    Date,
    Integer,
    Time,
    Timestamp,
    Timestamptz,
)
from piccolo.querystring import QueryString

from .type_conversion import Cast

###############################################################################
# Postgres / Cockroach

ExtractComponent = t.Literal[
    "century",
    "day",
    "decade",
    "dow",
    "doy",
    "epoch",
    "hour",
    "isodow",
    "isoyear",
    "julian",
    "microseconds",
    "millennium",
    "milliseconds",
    "minute",
    "month",
    "quarter",
    "second",
    "timezone",
    "timezone_hour",
    "timezone_minute",
    "week",
    "year",
]


class Extract(QueryString):
    def __init__(
        self,
        identifier: t.Union[Date, Time, Timestamp, Timestamptz, QueryString],
        datetime_component: ExtractComponent,
        alias: t.Optional[str] = None,
    ):
        """
        .. note:: This is for Postgres / Cockroach only.

        Extract a date or time component from a ``Date`` / ``Time`` /
        ``Timestamp`` / ``Timestamptz`` column. For example, getting the month
        from a timestamp:

        .. code-block:: python

            >>> from piccolo.query.functions import Extract
            >>> await Concert.select(
            ...     Extract(Concert.starts, "month", alias="start_month")
            ... )
            [{"start_month": 12}]

        :param identifier:
            Identifies the column.
        :param datetime_component:
            The date or time component to extract from the column.

        """
        if datetime_component.lower() not in t.get_args(ExtractComponent):
            raise ValueError("The date time component isn't recognised.")

        super().__init__(
            f"EXTRACT({datetime_component} FROM {{}})",
            identifier,
            alias=alias,
        )


###############################################################################
# SQLite


class Strftime(QueryString):
    def __init__(
        self,
        identifier: t.Union[Date, Time, Timestamp, Timestamptz, QueryString],
        datetime_format: str,
        alias: t.Optional[str] = None,
    ):
        """
        .. note:: This is for SQLite only.

        Format a datetime value. For example:

        .. code-block:: python

            >>> from piccolo.query.functions import Strftime
            >>> await Concert.select(
            ...     Strftime(Concert.starts, "%Y", alias="start_year")
            ... )
            [{"start_month": "2024"}]

        :param identifier:
            Identifies the column.
        :param datetime_format:
            A string describing the output format (see SQLite's
            `documentation <https://www.sqlite.org/lang_datefunc.html>`_
            for more info).

        """
        super().__init__(
            f"strftime('{datetime_format}', {{}})",
            identifier,
            alias=alias,
        )


###############################################################################
# Database agnostic


def _get_engine_type(identifier: t.Union[Column, QueryString]) -> str:
    if isinstance(identifier, Column):
        return identifier._meta.engine_type
    elif isinstance(identifier, QueryString) and (
        columns := identifier.columns
    ):
        return columns[0]._meta.engine_type
    else:
        raise ValueError("Unable to determine the engine type")


def _extract_component(
    identifier: t.Union[Date, Time, Timestamp, Timestamptz, QueryString],
    sqlite_format: str,
    postgres_format: ExtractComponent,
    alias: t.Optional[str],
) -> QueryString:
    engine_type = _get_engine_type(identifier=identifier)

    return Cast(
        (
            Strftime(
                identifier=identifier,
                datetime_format=sqlite_format,
            )
            if engine_type == "sqlite"
            else Extract(
                identifier=identifier,
                datetime_component=postgres_format,
            )
        ),
        Integer(),
        alias=alias,
    )


def Year(
    identifier: t.Union[Date, Timestamp, Timestamptz, QueryString],
    alias: t.Optional[str] = None,
) -> QueryString:
    """
    Extract the year as an integer.
    """
    return _extract_component(
        identifier=identifier,
        sqlite_format="%Y",
        postgres_format="year",
        alias=alias,
    )


def Month(
    identifier: t.Union[Date, Timestamp, Timestamptz, QueryString],
    alias: t.Optional[str] = None,
) -> QueryString:
    """
    Extract the month as an integer.
    """
    return _extract_component(
        identifier=identifier,
        sqlite_format="%m",
        postgres_format="month",
        alias=alias,
    )


def Day(
    identifier: t.Union[Date, Timestamp, Timestamptz, QueryString],
    alias: t.Optional[str] = None,
) -> QueryString:
    """
    Extract the day as an integer.
    """
    return _extract_component(
        identifier=identifier,
        sqlite_format="%d",
        postgres_format="day",
        alias=alias,
    )


def Hour(
    identifier: t.Union[Time, Timestamp, Timestamptz, QueryString],
    alias: t.Optional[str] = None,
) -> QueryString:
    """
    Extract the hour as an integer.
    """
    return _extract_component(
        identifier=identifier,
        sqlite_format="%H",
        postgres_format="hour",
        alias=alias,
    )


def Minute(
    identifier: t.Union[Time, Timestamp, Timestamptz, QueryString],
    alias: t.Optional[str] = None,
) -> QueryString:
    """
    Extract the minute as an integer.
    """
    return _extract_component(
        identifier=identifier,
        sqlite_format="%M",
        postgres_format="minute",
        alias=alias,
    )


def Second(
    identifier: t.Union[Time, Timestamp, Timestamptz, QueryString],
    alias: t.Optional[str] = None,
) -> QueryString:
    """
    Extract the second as an integer.
    """
    return _extract_component(
        identifier=identifier,
        sqlite_format="%S",
        postgres_format="second",
        alias=alias,
    )


__all__ = (
    "Extract",
    "Strftime",
    "Year",
    "Month",
    "Day",
    "Hour",
    "Minute",
    "Second",
)
