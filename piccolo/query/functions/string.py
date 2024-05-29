from .base import Function


class Upper(Function):
    function_name = "UPPER"


class Lower(Function):
    function_name = "LOWER"


class Ltrim(Function):
    function_name = "LTRIM"


class Rtrim(Function):
    function_name = "RTRIM"


__all__ = ("Upper", "Lower", "Ltrim", "Rtrim")
