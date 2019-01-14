from collections import OrderedDict
from itertools import groupby
import typing as t

from piccolo.query.base import Query
from piccolo.columns import Column, ForeignKey
from piccolo.query.mixins import (
    ColumnsMixin,
    CountMixin,
    DistinctMixin,
    LimitMixin,
    OrderByMixin,
    OutputMixin,
    WhereMixin,
)
from piccolo.querystring import QueryString

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
    def get_joins(self, columns: t.List[Column]) -> t.List[str]:
        """
        A call chain is a sequence of foreign keys representing joins which
        need to be made to retrieve a column in another table.
        """
        joins: t.List[str] = []
        for column in columns:
            _joins: t.List[str] = []
            for index, key in enumerate(column.call_chain, 0):
                table_alias = "$".join(
                    [
                        f"{_key._table.Meta.tablename}${_key._name}"
                        for _key in column.call_chain[: index + 1]
                    ]
                )
                key.table_alias = table_alias

                if index > 0:
                    left_tablename = column.call_chain[index - 1].table_alias
                else:
                    left_tablename = key._table.Meta.tablename

                _joins.append(
                    f"JOIN {key.references.Meta.tablename} {table_alias} "
                    f"ON ({left_tablename}.{key._name} = {table_alias}.id)"
                )

            joins.extend(_joins)

        # Remove duplicates
        return list(OrderedDict.fromkeys(joins))

    def check_valid_call_chain(self, keys: t.List[Column]) -> bool:
        for column in keys:
            if column.call_chain:
                # Make sure the call_chain isn't too large to discourage
                # very inefficient queries.

                if len(column.call_chain) > 10:
                    raise Exception(
                        "Joining more than 10 tables isn't supported - "
                        "please restructure your query."
                    )
        return True

    @property
    def querystring(self) -> QueryString:
        joins: t.List[str] = []

        if len(self.selected_columns) == 0:
            columns_str = "*"
        else:
            ###################################################################
            # JOIN

            self.check_valid_call_chain(self.selected_columns)

            joins = self.get_joins(self.selected_columns)

            ###################################################################

            column_names: t.List[str] = []
            for column in self.selected_columns:
                column_name = column._name

                if not column.call_chain:
                    column_names.append(
                        f"{self.table.Meta.tablename}.{column_name}"
                    )
                    continue

                column_name = (
                    "$".join([i._name for i in column.call_chain])
                    + f"${column_name}"
                )

                alias = f"{column.call_chain[-1].table_alias}.{column._name}"
                column_names.append(f'{alias} AS "{column_name}"')

            columns_str = ", ".join(column_names)

        #######################################################################

        select = "SELECT DISTINCT" if self.distinct else "SELECT"
        query = f'{select} {columns_str} FROM {self.table.Meta.tablename}'

        for join in joins:
            query += f" {join}"

        #######################################################################

        args: t.List[t.Any] = []

        if self._where:
            query += " WHERE {}"
            args.append(self._where.querystring)

        if self._order_by:
            query += " {}"
            args.append(self._order_by.querystring)

        if self._limit:
            query += " {}"
            args.append(self._limit.querystring)

        querystring = QueryString(query, *args)

        if self._count:
            querystring = QueryString(
                "SELECT COUNT(*) FROM ({}) AS sub_query",
                querystring
            )

        return querystring

    def __str__(self) -> str:
        return self.querystring.__str__()
