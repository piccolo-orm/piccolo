import typing as t
import uuid

from .base import Default


class UUID4(Default):
    @property
    def postgres(self):
        return "uuid_generate_v4()"

    @property
    def sqlite(self):
        return "''"

    def python(self):
        return uuid.uuid4()


UUIDArg = t.Union[UUID4, uuid.UUID, None]


__all__ = ["UUIDArg", "UUID4"]
