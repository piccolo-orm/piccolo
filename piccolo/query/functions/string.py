"""
These functions mirror their counterparts in the Postgresql docs:

https://www.postgresql.org/docs/current/functions-string.html

"""

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


__all__ = (
    "Length",
    "Lower",
    "Ltrim",
    "Reverse",
    "Rtrim",
    "Upper",
)
