from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.combination import And, Or, Where, WhereRaw  # noqa
    from piccolo.table import Table


Combinable = t.Union["Where", "WhereRaw", "And", "Or"]
Iterable = t.Iterable[t.Any]


TableInstance = t.TypeVar("TableInstance", bound="Table")
QueryResponseType = t.TypeVar("QueryResponseType", bound=t.Any)

ExtractField = t.Literal[
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


###############################################################################
# For backwards compatibility:

from piccolo.columns.defaults.timestamp import DatetimeDefault  # noqa
