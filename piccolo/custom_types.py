from enum import Enum
import datetime
import typing as t


if t.TYPE_CHECKING:
    from piccolo.columns.combination import Where, And, Or  # noqa


Combinable = t.Union["Where", "And", "Or"]
Iterable = t.Iterable[t.Any]


class DatetimeDefault(Enum):
    now = datetime.datetime.now


Datetime = t.Union[datetime.datetime, DatetimeDefault, None]


__all__ = ("Combinable", "Iterable", "Datetime")
