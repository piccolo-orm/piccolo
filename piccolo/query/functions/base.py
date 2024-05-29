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
        self._alias = alias

        if isinstance(identifier, Column):
            if not alias:
                self._alias = identifier._meta.get_default_alias()

            # We track any columns just in case we need to perform joins
            self.columns = [identifier, *getattr(self, "columns", [])]

            column_full_name = identifier._meta.get_full_name(with_alias=False)
            super().__init__(f"{self.function_name}({column_full_name})")
        elif isinstance(identifier, QueryString):
            if identifier._alias:
                self._alias = identifier._alias

            super().__init__(f"{self.function_name}({{}})", identifier)
        elif isinstance(identifier, str):
            super().__init__(f"{self.function_name}({{}})", identifier)
        else:
            raise ValueError("Unrecognised identifier type")
