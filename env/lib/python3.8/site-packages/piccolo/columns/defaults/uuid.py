import typing as t
import uuid
from enum import Enum

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


UUIDArg = t.Union[UUID4, uuid.UUID, str, Enum, None]


__all__ = ["UUIDArg", "UUID4"]
