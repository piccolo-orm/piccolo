import typing as t

from piccolo.columns.base import Column
from piccolo.querystring import QueryString


class Function(QueryString):
    function_name: str
    columns: t.List[Column]

    def __init__(
        self,
        identifier: t.Union[Column, QueryString, str],
        alias: t.Optional[str] = None,
    ):
        if isinstance(identifier, Column):
            # We track any columns just in case we need to perform joins
            self.columns = [identifier, *getattr(self, "columns", [])]

            column_full_name = identifier._meta.get_full_name(with_alias=False)
            super().__init__(
                f"{self.function_name}({column_full_name})",
                alias=alias,
            )
        elif isinstance(identifier, (QueryString, str)):
            super().__init__(
                f"{self.function_name}({{}})",
                identifier,
                alias=alias,
            )
        else:
            raise ValueError("Unrecognised identifier type")
