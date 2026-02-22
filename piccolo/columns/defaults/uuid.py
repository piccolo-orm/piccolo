import uuid
from collections.abc import Callable
from enum import Enum
from typing import Union

from .base import Default


class UUID4(Default):
    """
    This makes the default value for a
    :class:`UUID <piccolo.columns.column_types.UUID>` column a randomly
    generated UUID v4 value. The advantage over using :func:`uuid.uuid4` from
    the standard library, is the default is set on the column definition in the
    database too.
    """

    @property
    def postgres(self):
        return "gen_random_uuid()"

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
