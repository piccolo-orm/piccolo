from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeVar, Union

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.combination import And, Or, Where, WhereRaw  # noqa
    from piccolo.table import Table


Combinable = Union["Where", "WhereRaw", "And", "Or"]
CustomIterable = Iterable[Any]


TableInstance = TypeVar("TableInstance", bound="Table")
QueryResponseType = TypeVar("QueryResponseType", bound=Any)


###############################################################################
# For backwards compatibility:

from piccolo.columns.defaults.timestamp import DatetimeDefault  # noqa
