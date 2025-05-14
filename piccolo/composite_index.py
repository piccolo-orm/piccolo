from __future__ import annotations

import typing as t
from dataclasses import dataclass


@dataclass
class CompositeIndexMeta:
    """
    Composite index meta class for storing the composite index name
    although the name is only used for identification (can be any name)
    in migrations because Piccolo ``create_index`` method creates its own
    index name which is stored in the database.
    """

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


class CompositeIndex:
    """
    Composite indexes on the table.
    """

    _meta = CompositeIndexMeta()

    def __init__(
        self,
        columns: t.List[str],
    ) -> None:
        """
        :param columns:
            The table columns that should be composite index.
        """
        self.columns = columns
