from __future__ import annotations

import typing as t
from abc import abstractmethod
from dataclasses import dataclass, field


class Constraint:
    """
    All other constraints inherit from ``Constraint``. Don't use it directly.
    """

    def __init__(self, **kwargs) -> None:
        self._meta = ConstraintMeta(params=kwargs)

    def __hash__(self):
        return hash(self._meta.name)

    @property
    @abstractmethod
    def ddl(self) -> str:
        raise NotImplementedError


@dataclass
class ConstraintMeta:
    """
    This is used to store info about the constraint.
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


class UniqueConstraint(Constraint):
    """
    Unique constraint on the table columns.
    """

    def __init__(
        self,
        unique_columns: t.List[str],
        **kwargs,
    ) -> None:
        """
        :param unique_columns:
            The table columns that should be unique together.
        """
        self.unique_columns = unique_columns
        kwargs.update({"unique_columns": unique_columns})
        super().__init__(**kwargs)

    @property
    def ddl(self) -> str:
        unique_columns_string = ", ".join(self.unique_columns)
        return f"UNIQUE ({unique_columns_string})"
