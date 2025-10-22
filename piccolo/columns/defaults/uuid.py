import uuid
from collections.abc import Callable
from enum import Enum
from typing import Union

from piccolo.utils.uuid import uuid7

from .base import Default


class UUID4(Default):
    @property
    def postgres(self):
        """
        Historically we had to use `uuid_generate_v4()` from the `uuid-ossp`
        extension.

        Since Postgres 13 there is a built-in `gen_random_uuid` function which
        generates UUID v4 values.

        In Postgres 18, `uuidv4` was added, which is the same as
        `gen_random_uuid`, but more precisely named. We will move to this at
        some point in the future.

        """
        return "gen_random_uuid()"

    @property
    def cockroach(self):
        return self.postgres

    @property
    def sqlite(self):
        return "''"

    def python(self):
        return uuid.uuid4()


class UUID7(Default):
    @property
    def postgres(self):
        """
        Supported in Python 3.14 and above.
        """
        return "uuidv7()"

    @property
    def cockroach(self):
        # Supported?
        return self.postgres

    @property
    def sqlite(self):
        return "''"

    def python(self):
        return uuid7()


UUIDArg = Union[
    UUID4,
    UUID7,
    uuid.UUID,
    str,
    Enum,
    None,
    Callable[[], uuid.UUID],
]


__all__ = ["UUIDArg", "UUID4", "UUID7"]
