import typing as t

from ..base import Query
from ..mixins import (
    CountMixin, DistinctMixin, LimitMixin, OrderByMixin, OutputMixin,
    WhereMixin
)
if t.TYPE_CHECKING:
    from table import Table  # noqa


class Select(
    Query,
    CountMixin,
    DistinctMixin,
    LimitMixin,
    OrderByMixin,
    OutputMixin,
    WhereMixin,
):
    def __init__(self, table: 'Table', column_names: t.Iterable[str]) -> None:
        self.column_names = column_names
        super().__init__(table=table, base='')

    def __str__(self):
        if len(self.column_names) == 0:
            columns_str = '*'
        else:
            # TODO - make sure the columns passed in are valid
            column_names = []
            for column_name in self.column_names:
                if '.' in column_name:
                    alias = column_name.replace('.', '$.')
                    output_alias = column_name.replace('.', '$')
                    column_names.append(
                        f'{alias} AS "{output_alias}"'
                    )
                else:
                    column_names.append(column_name)

            columns_str = ', '.join(column_names)

        select = 'SELECT DISTINCT' if self.distinct else 'SELECT'
        query = f'{select} {columns_str} FROM "{self.table.Meta.tablename}"'

        #######################################################################

        # JOIN
        joins = []
        for column_name in self.column_names:
            if '.' in column_name:
                local_name, _ = column_name.split('.')
                table_name = self.table.get_column_by_name(
                    local_name
                ).references.Meta.tablename

                alias = f'{local_name}$'

                if alias in joins:
                    continue

                query += (
                    f' JOIN {table_name} {alias} ON {local_name} = {alias}.id'
                )
                joins.append(alias)

        #######################################################################

        if self._where:
            query += f' WHERE {self._where.__str__()}'

        if self._order_by:
            query += self._order_by.__str__()

        if self._limit:
            query += self._limit.__str__()

        if self._count:
            query = f'SELECT COUNT(*) FROM ({query}) AS sub_query'

        return query
