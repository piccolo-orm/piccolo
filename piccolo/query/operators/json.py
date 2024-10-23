from __future__ import annotations

import typing as t

from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json

if t.TYPE_CHECKING:
    from piccolo.columns.column_types import JSON


class Arrow(QueryString):
    """
    Allows you to drill into a JSON object.

    You can access this via the ``arrow`` function on ``JSON`` and ``JSONB``
    columns.

    """

    def __init__(
        self,
        identifier: t.Union[JSON, QueryString],
        key: t.Union[str, int, QueryString],
        alias: t.Optional[str] = None,
    ):
        super().__init__("{} -> {}", identifier, key, alias=alias)

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

    def arrow(self, key: t.Union[str, int, QueryString]) -> Arrow:
        """
        This allows you to drill multiple levels deep into a JSON object.

        For example::

            >>> await RecordingStudio.select(
            ...     RecordingStudio.name,
            ...     RecordingStudio.facilities.arrow(
            ...         "instruments"
            ...     ).arrow(
            ...         "drum_kits"
            ...     ).as_alias("drum_kits")
            ... ).output(load_json=True)
            [
                {'name': 'Abbey Road', 'drum_kits': 2},
                {'name': 'Electric Lady', 'drum_kits': 3}
            ]

        """
        return Arrow(identifier=self, key=key, alias=self._alias)
