from __future__ import annotations

import typing as t
from dataclasses import dataclass, field


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
    params: t.Dict[str, t.Any] = field(default_factory=dict)

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None

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
    """
    Composite index on the table columns.
    """

    def __init__(
        self,
        columns: t.List[str],
        **kwargs,
    ) -> None:
        """
        :param columns:
            The table columns that should be in composite index.
        """
        self.columns = columns
        kwargs.update({"columns": columns})
        super().__init__(**kwargs)
