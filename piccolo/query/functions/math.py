"""
These functions mirror their counterparts in the Postgresql docs:

https://www.postgresql.org/docs/current/functions-math.html

"""

from .base import Function


class Abs(Function):
    """
    Absolute value.
    """

    function_name = "ABS"


class Ceil(Function):
    """
    Nearest integer greater than or equal to argument.
    """

    function_name = "CEIL"


class Floor(Function):
    """
    Nearest integer less than or equal to argument.
    """

    function_name = "FLOOR"


class Round(Function):
    """
    Rounds to nearest integer.
    """

    function_name = "ROUND"


__all__ = (
    "Abs",
    "Ceil",
    "Floor",
    "Round",
)
