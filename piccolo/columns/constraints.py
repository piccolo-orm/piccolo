from .base import ColumnMeta, Column

class Constraint(Column):
    def __init__(self) -> None:
        pass

class UniqueConstraint(Constraint):
    """
    This class represents UNIQUE CONSTRAINT, which can be use to create
    many complex (multi-field) constraints for the Table
    All manipulations with the Constraint are like anything about Columns
    
    Usage:
        class FooTable(Table):
            foo_field = Text()
            bar_field = Text()
            my_constraint_1 = UniqueConstraint(['foo_field','bar_field'])

    SQL queries for creating and dropping constrains are similar to:
        ALTER TABLE foo_table ADD CONSTRAINT my_constraint_1 UNIQUE (foo_field, bar_field);
        ALTER TABLE foo_table DROP IF EXIST CONSTRAINT my_constraint_1;
    """
    def __init__(self, unique_columns: list[str]) -> None:
        super().__init__()
        self._meta = ColumnMeta()
        self.unique_columns = unique_columns
        self._meta.params.update({
             'unique_columns':self.unique_columns
        })

    @property
    def column_type(self):
        return "CONSTRAINT"

    @property
    def ddl(self) -> str:
        """
        Used when creating tables.
        """
        unique_columns_string = ",".join(self.unique_columns)
        query = f'{self.column_type} "{self._meta.db_column_name}" UNIQUE ({unique_columns_string})'
        return query