from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

from piccolo.querystring import QueryString
from piccolo.utils.encoding import dump_json

if TYPE_CHECKING:
    from piccolo.columns.column_types import JSON


class JSONQueryString(QueryString):

    def clean_value(self, value: Any):
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

    def engine(self) -> Union[str, None]:
        from piccolo.engine import engine_finder

        engine = engine_finder()
        return engine.engine_type if engine is not None else None


class GetChildElement(JSONQueryString):
    """
    Allows you to get a child element from a JSON object.

    You can access this via the ``arrow`` function on ``JSON`` and ``JSONB``
    columns.

    """

    def __init__(
        self,
        identifier: Union[JSON, QueryString],
        key: Union[str, int, QueryString],
        alias: Optional[str] = None,
    ):
        if isinstance(key, int):
            # asyncpg only accepts integer keys if we explicitly mark it as an
            # int.
            key = QueryString("{}::int", key)

        super().__init__("{} -> {}", identifier, key, alias=alias)

    def arrow(self, key: Union[str, int, QueryString]) -> GetChildElement:
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
        self, value: Union[str, int, QueryString]
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
        identifier: Union[JSON, QueryString],
        path: list[Union[str, int]],
        alias: Optional[str] = None,
    ):
        """
        :param path:
            For example: ``["technician", 0, "name"]``.

        """
        # we need to change the path to "".join(path) because MySQL needs
        # to use json path as a string like this ["$.message[0].name"] not
        # as a list of items ["message", 0, "name"] like Postgres
        path_ = [str(i) if isinstance(i, int) else i for i in path]
        super().__init__(
            "{} -> {}" if self.engine() == "mysql" else "{} #> {}",
            identifier,
            "".join(path_) if self.engine() == "mysql" else path_,
            alias=alias,
        )
