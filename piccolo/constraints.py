from __future__ import annotations

import typing as t
from abc import abstractmethod
from dataclasses import dataclass, field

from piccolo.columns import Column


class Constraint:
    """
    All other constraints inherit from ``Constraint``. Don't use it directly.
    """

    def __init__(self, name: str, **kwargs) -> None:
        self._meta = ConstraintMeta(name=name, params=kwargs)

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

    name: str

    # Used for representing the table in migrations.
    params: t.Dict[str, t.Any] = field(default_factory=dict)


class UniqueConstraint(Constraint):
    """
    Unique constraint on the table columns.
    """

    def __init__(
        self,
        *columns: Column,
        name: t.Optional[str] = None,
        nulls_distinct: bool = True,
    ) -> None:
        """
        :param columns:
            The table columns that should be unique together.
        :param name:
            The name of the constraint in the database. If not provided, we
            generate a sensible default.
        :param nulls_distinct:
            See the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS>`_
            for more information.

        """  # noqa: E501
        if len(columns) < 1:
            raise ValueError("At least 1 column must be specified.")

        tablenames = [column._meta.table._meta.tablename for column in columns]

        if len(set(tablenames)) > 1:
            raise ValueError("The columns belong to different tables.")

        column_names = [column._meta.db_column_name for column in columns]
        self.column_names = column_names

        if name is None:
            name = "_".join([tablenames[0], "unique", *column_names])
        self.name = name

        self.nulls_distinct = nulls_distinct

        super().__init__(
            name=name,
            column_names=column_names,
            nulls_distinct=nulls_distinct,
        )

    @property
    def ddl(self) -> str:
        nulls_string = (
            "NULLS NOT DISTINCT " if self.nulls_distinct is False else ""
        )
        columns_string = ", ".join(f'"{i}"' for i in self.column_names)
        return f"UNIQUE {nulls_string}({columns_string})"
