from __future__ import annotations

import math

from .base import Default


class Infinity(Default):

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


class NegativeInfinity(Default):

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


__all__ = [
    "Infinity",
    "NegativeInfinity",
]
