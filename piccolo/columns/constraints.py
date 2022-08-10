from .base import Selectable, ColumnMeta, Column

class Constraint(Column):
    def __init__(self) -> None:
        pass

class UniqueConstraint(Constraint):
    def __init__(self, unique_columns: list[str]) -> None:
        super().__init__()
        
        self._meta = ColumnMeta()
        self.unique_columns = unique_columns
        self._meta.params.update({
             'unique_columns':self.unique_columns
        })

#ALTER TABLE policies ADD CONSTRAINT constraint_test_1 UNIQUE (permission, role);
#ALTER TABLE policies DROP CONSTRAINT constraint_test_1;
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
    
    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        """
        How to refer to this column in a SQL query, taking account of any joins
        and aliases.
        """
        if with_alias:
            if self._alias:
                original_name = self._meta.get_full_name(
                    with_alias=False,
                )
                return f'{original_name} AS "{self._alias}"'
            else:
                return self._meta.get_full_name(
                    with_alias=True,
                )

        return self._meta.get_full_name(with_alias=False)