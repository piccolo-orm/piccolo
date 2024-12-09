from __future__ import annotations

import typing as t

from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json

if t.TYPE_CHECKING:
    from piccolo.columns.column_types import JSON


class JSONQueryString(QueryString):

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


class GetChildElement(JSONQueryString):
    """
    Allows you to get a child element from a JSON object.

    You can access this via the ``arrow`` function on ``JSON`` and ``JSONB``
    columns.

    """

    def __init__(
        self,
        identifier: t.Union[JSON, QueryString],
        key: t.Union[str, int, QueryString],
        alias: t.Optional[str] = None,
    ):
        if isinstance(key, int):
            # asyncpg only accepts integer keys if we explicitly mark it as an
            # int.
            key = QueryString("{}::int", key)

        super().__init__("{} -> {}", identifier, key, alias=alias)

    def arrow(self, key: t.Union[str, int, QueryString]) -> GetChildElement:
        """
        This allows you to drill multiple levels deep into a JSON object if
        needed.

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
        return GetChildElement(identifier=self, key=key, alias=self._alias)

    def __getitem__(
        self, value: t.Union[str, int, QueryString]
    ) -> GetChildElement:
        return GetChildElement(identifier=self, key=value, alias=self._alias)


class GetElementFromPath(JSONQueryString):
    """
    Allows you to retrieve an element from a JSON object by specifying a path.
    It can be several levels deep.

    You can access this via the ``from_path`` function on ``JSON`` and
    ``JSONB`` columns.

    """

    def __init__(
        self,
        identifier: t.Union[JSON, QueryString],
        path: t.List[t.Union[str, int]],
        alias: t.Optional[str] = None,
    ):
        """
        :param path:
            For example: ``["technician", 0, "name"]``.

        """
        super().__init__(
            "{} #> {}",
            identifier,
            [str(i) if isinstance(i, int) else i for i in path],
            alias=alias,
        )
