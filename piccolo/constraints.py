from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from piccolo.columns import Column
    from piccolo.custom_types import Combinable


@dataclass
class ConstraintMeta:
    """
    This is used to store info about the constraint for migrations.
    """

    _name: str | None

    # Used for representing the table in migrations.
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "name should have been passed into the constraint or set in "
                "the TableMetaclass."
            )
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value


class Constraint(metaclass=ABCMeta):
    """
    All other constraints inherit from ``Constraint``. Don't use it directly.
    """

    def __init__(self, name: str | None = None, **kwargs) -> None:
        self._meta = ConstraintMeta(_name=name, params=kwargs)

    def __hash__(self):
        return hash(self._meta._name)

    @property
    @abstractmethod
    def ddl(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _table_str(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def serialise_self(self):
        raise NotImplementedError


###############################################################################


class Unique(Constraint):
    """
    Add a unique constraint to one or more columns. For example::

        from piccolo.constraints import Unique

        class Album(Table):
            name = Varchar()
            band = ForeignKey(Band)

            unique_name_band = Unique([name, band])


    In the above example, the database will enforce that ``name`` and
    ``band`` form a unique combination.

    :param columns:
        The table columns that should be unique together.
    :param nulls_distinct:
        See the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS>`_
        for more information.

    """  # noqa: E501

    def __init__(
        self,
        columns: list[Union[Column, str]],
        nulls_distinct: bool = True,
        name: str | None = None,
    ):
        if len(columns) < 1:
            raise ValueError("At least 1 column must be specified.")

        self.columns = columns
        self.nulls_distinct = nulls_distinct
        super().__init__(
            name=name, columns=columns, nulls_distinct=nulls_distinct
        )

    def get_column_names(self):
        from piccolo.columns import Column

        return [
            (
                column._meta.db_column_name
                if isinstance(column, Column)
                else column
            )
            for column in self.columns
        ]

    def serialise_self(self):
        """
        Convert any column references to strings, so it can more easily be
        output to migrations.

        You should wait for the ``Table`` metaclass to assign names to all of
        the columns before calling this method.
        """
        self._meta.params["columns"] = self.get_column_names()

    @property
    def ddl(self) -> str:
        nulls_string = (
            "NULLS NOT DISTINCT " if self.nulls_distinct is False else ""
        )
        column_names = self.get_column_names()
        columns_string = ", ".join(f'"{i}"' for i in column_names)
        return f"UNIQUE {nulls_string}({columns_string})"

    def _table_str(self) -> str:
        column_names = self.get_column_names()

        columns_string = ", ".join(
            [f'"{column_name}"' for column_name in column_names]
        )
        return (
            f"{self._meta._name} = Unique([{columns_string}], "
            f"nulls_distinct={self.nulls_distinct})"
        )


###############################################################################


class Check(Constraint):
    """
    Add a check constraint to the table. For example::

        from piccolo.constraints import Check

        class Ticket(Table):
            price = Decimal()

            check_price_positive = Check(price >= 0)

    You can have more complex conditions. For example::

        from piccolo.constraints import Check

        class Ticket(Table):
            price = Decimal()

            check_price_range = Check(
                (price >= 0) & (price < 100)
            )

    :param condition:
        The syntax is the same as the ``where`` clause used by most
        queries (e.g. ``select``).

    """

    def __init__(
        self,
        condition: Union[Combinable, str],
        name: str | None = None,
    ):
        """
        :param condition:
            The SQL expression used to make sure the data is valid (e.g.
            ``"price > 0"``).
        :param name:
            The name of the constraint in the database.

        """
        self.condition = condition
        super().__init__(name=name, condition=condition)

    def get_condition_str(self) -> str:
        from piccolo.columns.combination import CombinableMixin

        if isinstance(self.condition, CombinableMixin):
            return self.condition.querystring_for_constraint.__str__()
        else:
            return self.condition

    def serialise_self(self):
        """
        You should wait for the ``Table`` metaclass to assign names to all of
        the columns before calling this method.
        """
        self._meta.params["condition"] = self.get_condition_str()

    @property
    def ddl(self) -> str:
        return f"CHECK ({self.get_condition_str()})"

    def _table_str(self) -> str:
        return f'{self._meta._name} = Check("{self.get_condition_str()}")'
