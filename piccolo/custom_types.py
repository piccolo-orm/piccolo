from __future__ import annotations

import datetime
import decimal
import uuid
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeVar, Union

from typing_extensions import TypeAlias

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.combination import And, Or, Where, WhereRaw  # noqa
    from piccolo.table import Table


Combinable = Union["Where", "WhereRaw", "And", "Or"]
CustomIterable = Iterable[Any]


TableInstance = TypeVar("TableInstance", bound="Table")
QueryResponseType = TypeVar("QueryResponseType", bound=Any)


# These are types we can reasonably expect to send to the database.
BasicTypes: TypeAlias = Union[
    bytes,
    datetime.date,
    datetime.datetime,
    datetime.time,
    datetime.timedelta,
    decimal.Decimal,
    dict,
    float,
    int,
    list,
    str,
    uuid.UUID,
]

###############################################################################
# For backwards compatibility:

from piccolo.columns.defaults.timestamp import DatetimeDefault  # noqa
