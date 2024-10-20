from __future__ import annotations

import typing as t

from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json

if t.TYPE_CHECKING:
    from piccolo.columns.column_types import JSONB


class Arrow(QueryString):
    """
    Functionally this is basically the same as ``QueryString``, we just need
    ``Query._process_results`` to be able to differentiate it from a normal
    ``QueryString`` just in case the user specified
    ``.output(load_json=True)``.
    """

    def __init__(self, column: JSONB, key: str, alias: t.Optional[str] = None):
        super().__init__("{} -> {}", column, key, alias=alias)

    def clean_value(self, value: t.Any):
        if not isinstance(value, (str, QueryString)):
            value = dump_json(value)
        return value

    def __eq__(self, value) -> QueryString:  # type: ignore[override]
        value = self.clean_value(value)
        return QueryString("{} = {}", self, value)

    def __ne__(self, value) -> QueryString:  # type: ignore[override]
        value = self.clean_value(value)
        return QueryString("{} != {}", self, value)

    def eq(self, value) -> QueryString:
        return self.__eq__(value)

    def ne(self, value) -> QueryString:
        return self.__ne__(value)
