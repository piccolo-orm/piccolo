import typing as t

from piccolo.columns.column_types import Date, Time, Timestamp, Timestamptz
from piccolo.querystring import QueryString

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
        date_time_component: ExtractComponent,
        alias: t.Optional[str] = None,
    ):
        """
        Extract a date or time component from a ``Date`` / ``Time`` /
        ``Timestamp`` / ``Timestamptz`` column. For example, getting the month
        from a timestamp.

            >>> from piccolo.query.functions import Extract

            >>> await Concert.select(
            ...     Extract(Concert.starts, "month", alias="start_month")
            ... )
            [{"start_month": 12}]

        :param identifier:
            Identifies the column.
        :param date_time_component:
            The date or time component to extract from the column.

        """
        if date_time_component.lower() not in t.get_args(ExtractComponent):
            raise ValueError("The date time component isn't recognised.")

        super().__init__(
            f"EXTRACT({date_time_component} FROM {{}})",
            identifier,
            alias=alias,
        )


__all__ = ("Extract",)
