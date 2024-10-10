import typing as t

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class Function(QueryString):
    function_name: str

    def __init__(
        self,
        identifier: t.Union[Column, QueryString, str],
        alias: t.Optional[str] = None,
    ):
        alias = alias or self.__class__.__name__.lower()

        super().__init__(
            f"{self.function_name}({{}})",
            identifier,
            alias=alias,
        )
