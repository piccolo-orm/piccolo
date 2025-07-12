from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


class Composite:
    """
    All other composite indexes inherit from ``Composite``.
    Don't use it directly.
    """

    def __init__(self, **kwargs) -> None:
        self._meta = CompositeMeta(params=kwargs)

    def __hash__(self):
        return hash(self._meta.name)


@dataclass
class CompositeMeta:
    """
    This is used to store info about the composite index.
    """

    # Used for representing the table in migrations.
    params: dict[str, Any] = field(default_factory=dict)

    # Set by the Table Metaclass:
    _name: Optional[str] = None

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "`_name` isn't defined - the Table Metaclass should set it."
            )
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value


class CompositeIndex(Composite):

    def __init__(
        self,
        columns: list[str],
        **kwargs,
    ) -> None:
        """
        Add a composite index to multiple columns. For example::

            from piccolo.columns import Varchar, Boolean
            from piccolo.composite_index import CompositeIndex
            from piccolo.table import Table

            class Album(Table):
                name = Varchar()
                released = Boolean(default=False)
                name_released_idx = CompositeIndex(["name", "released"])

        This way we create composite index ``name_released_idx``
        on ``Album`` table.

        To drop the composite index, simply delete or comment out
        the composite index argument and perform another migration.

        :param columns:
            The table column name that should be in composite index.

        """
        self.columns = columns
        kwargs.update({"columns": columns})
        super().__init__(**kwargs)
