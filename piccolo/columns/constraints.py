import typing as t

from .base import Column, ColumnMeta


class Constraint(Column):
    def __init__(self) -> None:
        pass


class UniqueConstraint(Constraint):
    """
    Used for applying unique constraint to multiple columns in the table.

    **Example**

    .. code-block:: python

        class FooTable(Table):
            foo_field = Text()
            bar_field = Text()
            my_constraint_1 = UniqueConstraint(['foo_field', 'bar_field'])
    """

    def __init__(self, unique_columns: t.List[str]) -> None:
        if len(unique_columns) < 2:
            raise ValueError("unique_columns must contain at least 2 columns")
        super().__init__()
        self._meta = ColumnMeta()
        self.unique_columns = unique_columns
        self._meta.params.update({"unique_columns": self.unique_columns})

    @property
    def column_type(self):
        return "CONSTRAINT"

    @property
    def ddl(self) -> str:
        unique_columns_string = ",".join(self.unique_columns)
        query = f'{self.column_type} "{self._meta.db_column_name}" UNIQUE ({unique_columns_string})'  # noqa: E501
        return query
