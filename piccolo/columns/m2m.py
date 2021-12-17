from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass

from piccolo.columns.base import Selectable
from piccolo.columns.column_types import Column, ForeignKey, LazyTableReference

if t.TYPE_CHECKING:
    from piccolo.table import Table


class M2MSelect(Selectable):
    """
    This is a subquery used within a select to fetch data via an M2M table.
    """

    def __init__(self, column: Column, m2m: M2M):
        """
        :param column:
            Which column to include from the related table.

        """
        self.column = column
        self.m2m = m2m

    def get_select_string(self, engine_type: str, just_alias=False) -> str:
        m2m_table_name = self.m2m._meta.resolved_joining_table._meta.tablename
        m2m_relationship_name = self.m2m._meta.name

        fk_1 = self.m2m._meta.foreign_key_columns[0]
        fk_1_name = fk_1._meta.db_column_name
        table_1 = fk_1._foreign_key_meta.resolved_references
        table_1_name = table_1._meta.tablename
        table_1_pk_name = table_1._meta.primary_key._meta.db_column_name

        fk_2 = self.m2m._meta.foreign_key_columns[1]
        fk_2_name = fk_2._meta.db_column_name
        table_2 = fk_2._foreign_key_meta.resolved_references
        table_2_name = table_2._meta.tablename
        table_2_pk_name = table_2._meta.primary_key._meta.db_column_name

        column_name = self.column._meta.db_column_name

        return f"""
            ARRAY(
                SELECT
                inner_{table_2_name}.{column_name}
                from {m2m_table_name}
                join {table_1_name} inner_{table_1_name} on (
                    {m2m_table_name}.{fk_1_name} = inner_{table_1_name}.{table_1_pk_name}
                )
                join {table_2_name} inner_{table_2_name} on (
                    {m2m_table_name}.{fk_2_name} = inner_{table_2_name}.{table_2_pk_name}
                )
                where {m2m_table_name}.{fk_1_name} = {table_1_name}.{table_1_pk_name}
            ) as {m2m_relationship_name}
        """  # noqa: E501


@dataclass
class M2MMeta:
    joining_table: t.Union[t.Type[Table], LazyTableReference]
    _foreign_key_columns: t.Optional[t.List[ForeignKey]] = None

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None
    _table: t.Optional[t.Type[Table]] = None

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "`_name` isn't defined - the Table Metaclass should set it."
            )
        return self._name

    @property
    def resolved_joining_table(self) -> t.Type[Table]:
        """
        Evaluates the ``joining_table`` attribute if it's a
        ``LazyTableReference``, raising a ``ValueError`` if it fails, otherwise
        returns a ``Table`` subclass.
        """
        from piccolo.table import Table

        if isinstance(self.joining_table, LazyTableReference):
            return self.joining_table.resolve()
        elif inspect.isclass(self.joining_table) and issubclass(
            self.joining_table, Table
        ):
            return self.joining_table
        else:
            raise ValueError(
                "The joining_table attribute is neither a Table subclass or a "
                "LazyTableReference instance."
            )

    @property
    def foreign_key_columns(self) -> t.List[ForeignKey]:
        if not self._foreign_key_columns:
            self._foreign_key_columns = (
                self.resolved_joining_table._meta.foreign_key_columns[0:2]
            )
        return self._foreign_key_columns


class M2M:
    def __init__(
        self,
        joining_table: t.Union[t.Type[Table], LazyTableReference],
        foreign_key_columns: t.Optional[t.List[ForeignKey]] = None,
    ):
        """
        :param joining_table:
            A ``Table`` containing two ``ForeignKey`` columns.
        :param foreign_key_columns:
            If for some reason your joining table has more than two foreign key
            columns, you can explicitly specify which two are relevant.

        """
        if foreign_key_columns:
            if len(foreign_key_columns) != 2 or not all(
                isinstance(i, ForeignKey) for i in foreign_key_columns
            ):
                raise ValueError("You must specify two ForeignKey columns.")

        self._meta = M2MMeta(
            joining_table=joining_table,
            _foreign_key_columns=foreign_key_columns,
        )

    def __call__(self, column: Column) -> Selectable:
        """
        :param column:
            Which column to include from the related table.

        """
        return M2MSelect(column, m2m=self)
