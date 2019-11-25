import datetime
import typing as t


if t.TYPE_CHECKING:
    from piccolo.columns.combination import Where, And, Or  # noqa


Combinable = t.Union["Where", "And", "Or"]
Iterable = t.Iterable[t.Any]
Datetime = t.Union[datetime.datetime, t.Callable[[], datetime.datetime], None]


__all__ = ("Combinable", "Iterable", "Datetime")
