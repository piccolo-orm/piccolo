from dataclasses import dataclass
from enum import Enum
import datetime
import typing as t
import uuid


if t.TYPE_CHECKING:
    from piccolo.columns.combination import Where, And, Or  # noqa


Combinable = t.Union["Where", "And", "Or"]
Iterable = t.Iterable[t.Any]


@dataclass
class Default:
    python: t.Callable
    postgres: str
    sqlite: str


class DatetimeDefault(Enum):
    now = Default(
        python=datetime.datetime.now,
        postgres="current_timestamp",
        sqlite="current_timestamp",
    )


class UUIDDefault(Enum):
    uuid4 = Default(
        python=uuid.uuid4, postgres="uuid_generate_v4()", sqlite="''"
    )


UUID_ = t.Union[UUIDDefault, uuid.UUID]
Datetime = t.Union[datetime.datetime, DatetimeDefault, None]


__all__ = (
    "Combinable",
    "Iterable",
    "Datetime",
    "DatetimeDefault",
    "Default",
    "UUID_",
    "UUIDDefault",
)
