from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from piccolo.custom_types import BasicTypes
from piccolo.querystring import QueryString

if TYPE_CHECKING:
    from piccolo.columns import Column


class Coalesce(QueryString):
    def __init__(
        self,
        *args: Union[Column, QueryString, BasicTypes],
        alias: Optional[str] = None,
    ):
        """
        Returns the first non-null value.
        """
        if len(args) < 2:
            raise ValueError("At least two values must be passed in.")

        placeholders = ", ".join("{}" for _ in args)

        super().__init__(f"COALESCE({placeholders})", *args, alias=alias)
