from .base import Function


class Upper(Function):
    function_name = "UPPER"


class Lower(Function):
    function_name = "LOWER"


__all__ = ("Upper", "Lower")
