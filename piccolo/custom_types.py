from __future__ import annotations
import typing as t


if t.TYPE_CHECKING:
    from piccolo.columns.combination import Where, And, Or  # noqa


Combinable = t.Union["Where", "And", "Or"]
Iterable = t.Iterable[t.Any]


###############################################################################
# For backwards compatibility:

from piccolo.columns.defaults.timestamp import DatetimeDefault  # noqa
