import uuid
from collections.abc import Callable
from enum import Enum
from typing import Union

from .base import Default


class UUID4(Default):
    @property
    def postgres(self):
        return "uuid_generate_v4()"

    @property
    def cockroach(self):
        return self.postgres

    @property
    def sqlite(self):
        return "''"

    def python(self):
        return uuid.uuid4()


UUIDArg = Union[UUID4, uuid.UUID, str, Enum, None, Callable[[], uuid.UUID]]


__all__ = ["UUIDArg", "UUID4"]
