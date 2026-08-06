from __future__ import annotations

import decimal
from enum import Enum
from typing import Callable, Union

from .base import Default


class InfinityDecimal(Default):

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
        return decimal.Decimal("Infinity")


class NegativeInfinityDecimal(Default):

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
        return decimal.Decimal("-Infinity")


NumericArg = Union[
    decimal.Decimal,
    Enum,
    InfinityDecimal,
    NegativeInfinityDecimal,
    Callable[[], decimal.Decimal],
    None,
]


__all__ = [
    "InfinityDecimal",
    "NegativeInfinityDecimal",
    "NumericArg",
]
