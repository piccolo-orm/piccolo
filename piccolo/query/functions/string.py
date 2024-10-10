"""
These functions mirror their counterparts in the Postgresql docs:

https://www.postgresql.org/docs/current/functions-string.html

"""

import typing as t

from piccolo.columns.base import Column
from piccolo.columns.column_types import Text, Varchar
from piccolo.querystring import QueryString

from .base import Function


class Length(Function):
    """
    Returns the number of characters in the string.
    """

    function_name = "LENGTH"


class Lower(Function):
    """
    Converts the string to all lower case, according to the rules of the
    database's locale.
    """

    function_name = "LOWER"


class Ltrim(Function):
    """
    Removes the longest string containing only characters in characters (a
    space by default) from the start of string.
    """

    function_name = "LTRIM"


class Reverse(Function):
    """
    Return reversed string.

    Not supported in SQLite.

    """

    function_name = "REVERSE"


class Rtrim(Function):
    """
    Removes the longest string containing only characters in characters (a
    space by default) from the end of string.
    """

    function_name = "RTRIM"


class Upper(Function):
    """
    Converts the string to all upper case, according to the rules of the
    database's locale.
    """

    function_name = "UPPER"


class Concat(QueryString):
    def __init__(
        self,
        *args: t.Union[Column, QueryString, str],
        alias: t.Optional[str] = None,
    ):
        """
        Concatenate multiple values into a single string.

        .. note::
            Null values are ignored, so ``null + '!!!'`` returns ``!!!``,
            not ``null``.

        .. warning::
            For SQLite, this is only available in version 3.44.0 and above.

        """
        if len(args) < 2:
            raise ValueError("At least two values must be passed in.")

        placeholders = ", ".join("{}" for _ in args)

        processed_args: t.List[t.Union[QueryString, Column]] = []

        for arg in args:
            if isinstance(arg, str) or (
                isinstance(arg, Column)
                and not isinstance(arg, (Varchar, Text))
            ):
                processed_args.append(QueryString("CAST({} AS TEXT)", arg))
            else:
                processed_args.append(arg)

        super().__init__(
            f"CONCAT({placeholders})", *processed_args, alias=alias
        )


__all__ = (
    "Length",
    "Lower",
    "Ltrim",
    "Reverse",
    "Rtrim",
    "Upper",
    "Concat",
)
