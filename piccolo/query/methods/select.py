from itertools import groupby
import typing as t

from ..base import Query
from ..mixins import (
    ColumnsMixin, CountMixin, DistinctMixin, LimitMixin, OrderByMixin,
    OutputMixin, WhereMixin
)
if t.TYPE_CHECKING:
    from table import Table  # noqa


class Select(
    Query,
    ColumnsMixin,
    CountMixin,
    DistinctMixin,
    LimitMixin,
    OrderByMixin,
    OutputMixin,
    WhereMixin,
):
    def __str__(self):
        joins = []

        if len(self.selected_columns) == 0:
            columns_str = '*'
        else:
            ###################################################################
            # JOIN

            keys = set()

            for column in self.selected_columns:
                if column.call_chain:
                    # TODO: Only works one deep at the moment - needs work.
                    for key in column.call_chain[:1]:
                        keys.add(key)

            keys = list(keys)
            grouped_keys = groupby(
                keys,
                key=lambda k: k.references.Meta.tablename
            )

            for tablename, __keys in grouped_keys:
                _keys = [i for i in __keys]
                for index, _key in enumerate(_keys):
                    _index = index + 1
                    _key.index = _index
                    # Double underscore is just to prevent the likelihood of a
                    # name clash.
                    alias = f'{tablename}__{_index}'
                    _key.alias = alias
                    joins.append(
                        f' JOIN {tablename} {alias} ON {_key._name} = {alias}.id'
                    )

            ###################################################################

            column_names = []
            for column in self.selected_columns:
                column_name = column._name

                if not column.call_chain:
                    column_names.append(
                        f'{self.table.Meta.tablename}.{column_name}'
                    )
                    continue

                column_name = '$'.join([
                    i._name for i in column.call_chain
                ]) + f'${column_name}'

                alias = f'{column.call_chain[0].alias}.{column._name}'
                column_names.append(
                    f'{alias} AS "{column_name}"'
                )

            columns_str = ', '.join(column_names)

        #######################################################################

        select = 'SELECT DISTINCT' if self.distinct else 'SELECT'
        query = f'{select} {columns_str} FROM "{self.table.Meta.tablename}"'

        for join in joins:
            query += join

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
