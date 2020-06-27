from dataclasses import dataclass
from enum import Enum
import datetime
import typing as t
import uuid


if t.TYPE_CHECKING:
    from piccolo.columns.combination import Where, And, Or  # noqa


Combinable = t.Union["Where", "And", "Or"]
Iterable = t.Iterable[t.Any]


###############################################################################


@dataclass
class Default:
    python: t.Callable
    postgres: str
    sqlite: str


class TimestampDefault(Enum):
    now = Default(
        python=datetime.datetime.now,
        postgres="current_timestamp",
        sqlite="current_timestamp",
    )


# To preserve backwards compatibility:
DatetimeDefault = TimestampDefault


class DateDefault(Enum):
    now = Default(
        python=lambda: datetime.datetime.now().date(),
        postgres="current_date",
        sqlite="current_date",
    )


class TimeDefault(Enum):
    now = Default(
        python=lambda: datetime.datetime.now().time(),
        postgres="current_time",
        sqlite="current_time",
    )


class UUIDDefault(Enum):
    uuid4 = Default(
        python=uuid.uuid4, postgres="uuid_generate_v4()", sqlite="''"
    )


UUIDArg = t.Union[UUIDDefault, uuid.UUID]
TimestampArg = t.Union[datetime.datetime, TimestampDefault, None]
DateArg = t.Union[datetime.date, DateDefault, None]
TimeArg = t.Union[datetime.time, TimeDefault, None]
