from __future__ import annotations

import typing as t
from dataclasses import dataclass


@dataclass
class Choice:
    """
    When defining enums for ``Column`` choices, they can either be defined
    like:

    .. code-block:: python

        class Title(Enum):
            mr = 1
            mrs = 2

    If using Piccolo Admin, the values shown will be ``Mr`` and ``Mrs``. If you
    want more control, you can use ``Choice`` for the value instead.

    .. code-block:: python

        class Title(Enum):
            mr = Choice(value=1, display_name="Mr.")
            mrs = Choice(value=1, display_name="Mrs.")

    Now the values shown will be ``Mr.`` and ``Mrs.``.

    """

    value: t.Any
    display_name: str
