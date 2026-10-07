from __future__ import annotations

import math
from enum import Enum
from typing import Callable, Union

from .base import Default


class InfinityFloat(Default):
    """
    ``math.inf`` in Python.
    """

    @property
    def postgres(self):
        return "'Infinity'"

    @property
    def cockroach(self):
        return "'Infinity'"

    @property
    def sqlite(self):
        return "'Infinity'"

    def python(self):
        return math.inf


class NegativeInfinityFloat(Default):
    """
    ``-1 * math.inf`` in Python.
    """

    @property
    def postgres(self):
        return "'-Infinity'"

    @property
    def cockroach(self):
        return "'-Infinity'"

    @property
    def sqlite(self):
        return "'-Infinity'"

    def python(self):
        return math.inf * -1


RealArg = Union[
    float,
    Enum,
    InfinityFloat,
    NegativeInfinityFloat,
    Callable[[], float],
    None,
]


__all__ = [
    "InfinityFloat",
    "NegativeInfinityFloat",
    "RealArg",
]
