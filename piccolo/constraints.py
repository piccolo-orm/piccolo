from __future__ import annotations

import typing as t
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field

if t.TYPE_CHECKING:
    from piccolo.columns import Column
    from piccolo.custom_types import Combinable


class ConstraintConfig(metaclass=ABCMeta):

    @abstractmethod
    def to_constraint(self, tablename: str) -> Constraint:
        """
        Override in subclasses.
        """
        raise NotImplementedError()


class Unique(ConstraintConfig):
    """
    Add a unique constraint to one or more columns. For example::

        from piccolo.constraints import Unique

        class Album(Table):
            name = Varchar()
            band = ForeignKey(Band)

            constraints = [
                Unique([name, band])
            ]

    In the above example, the database will enforce that ``name`` and
    ``band`` form a unique combination.

    :param columns:
        The table columns that should be unique together.
    :param name:
        The name of the constraint in the database. If not provided, we
        generate a sensible default.
    :param nulls_distinct:
        See the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS>`_
        for more information.

    """  # noqa: E501

    def __init__(
        self,
        columns: t.List[t.Union[Column, str]],
        name: t.Optional[str] = None,
        nulls_distinct: bool = True,
    ):
        if len(columns) < 1:
            raise ValueError("At least 1 column must be specified.")

        self.columns = columns
        self.name = name
        self.nulls_distinct = nulls_distinct

    def to_constraint(self, tablename: str) -> UniqueConstraint:
        """
        You should wait for the ``Table`` metaclass to assign names all of the
        columns before calling this method.
        """
        from piccolo.columns import Column

        column_names = [
            (
                column._meta.db_column_name
                if isinstance(column, Column)
                else column
            )
            for column in self.columns
        ]

        name = self.name or "_".join(["unique", tablename, *column_names])

        return UniqueConstraint(
            column_names=column_names,
            name=name,
            nulls_distinct=self.nulls_distinct,
        )


class Check(ConstraintConfig):
    """
    Add a check constraint to the table. For example::

        from piccolo.constraints import Check

        class Ticket(Table):
            price = Decimal()

            constraints = [
                Check(price >= 0)
            ]

    You can have more complex conditions. For example::

        from piccolo.constraints import Check

        class Ticket(Table):
            price = Decimal()

            constraints = [
                Check(
                    (price >= 0) & (price < 100)
                )
            ]

    :param condition:
        The syntax is the same as the ``where`` clause used by most
        queries (e.g. ``select``).
    :param name:
        The name of the constraint in the database. If not provided, we
        generate a sensible default.

    """

    def __init__(
        self,
        condition: t.Union[Combinable, str],
        name: t.Optional[str] = None,
    ):
        self.condition = condition
        self.name = name

    def to_constraint(self, tablename: str) -> CheckConstraint:
        """
        You should wait for the ``Table`` metaclass to assign names all of the
        columns before calling this method.
        """
        from piccolo.columns.combination import CombinableMixin

        name = self.name

        if name is None:
            if isinstance(self.condition, str):
                name = "_".join(
                    ["check", tablename, str(hash(self.condition))]
                )
            else:
                from piccolo.query.mixins import WhereDelegate

                columns = WhereDelegate(
                    _where=self.condition
                ).get_where_columns()
                column_names = [
                    column._meta.db_column_name for column in columns
                ]
                name = "_".join(["check", tablename, *column_names])

        if isinstance(self.condition, CombinableMixin):
            condition_str = self.condition.querystring_for_constraint.__str__()
        else:
            condition_str = self.condition

        return CheckConstraint(
            condition=condition_str,
            name=name,
        )


###############################################################################


class Constraint(metaclass=ABCMeta):
    """
    All other constraints inherit from ``Constraint``. Don't use it directly.
    """

    def __init__(self, name: str, **kwargs) -> None:
        kwargs.update(name=name)
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

    This is the internal representation that Piccolo uses for constraints -
    the user just supplies ``Unique``.
    """

    def __init__(
        self,
        column_names: t.Sequence[str],
        name: str,
        nulls_distinct: bool = True,
    ) -> None:
        """
        :param columns:
            The table columns that should be unique together.
        :param name:
            The name of the constraint in the database.
        :param nulls_distinct:
            See the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-UNIQUE-CONSTRAINTS>`_
            for more information.

        """  # noqa: E501
        if len(column_names) < 1:
            raise ValueError("At least 1 column must be specified.")

        self.column_names = column_names
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


class CheckConstraint(Constraint):
    """
    Check constraint on the table.

    This is the internal representation that Piccolo uses for constraints -
    the user just supplies ``Check``.
    """

    def __init__(
        self,
        condition: str,
        name: str,
    ) -> None:
        """
        :param condition:
            The SQL expression used to make sure the data is valid (e.g.
            ``"price > 0"``).
        :param name:
            The name of the constraint in the database.

        """
        self.condition = condition
        super().__init__(name=name, condition=condition)

    @property
    def ddl(self) -> str:
        return f"CHECK ({self.condition})"
