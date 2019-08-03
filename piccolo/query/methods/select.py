from __future__ import annotations
from collections import OrderedDict
import typing as t

from piccolo.query.base import Query
from piccolo.columns import Column
from piccolo.query.mixins import (
    ColumnsDelegate,
    CountDelegate,
    DistinctDelegate,
    LimitDelegate,
    OrderByDelegate,
    OutputDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from table import Table  # noqa
    from piccolo.custom_types import Combinable


class Select(Query):

    def setup_delegates(self):
        self.columns_delegate = ColumnsDelegate()
        self.count_delegate = CountDelegate()
        self.distinct_delegate = DistinctDelegate()
        self.limit_delegate = LimitDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.where_delegate = WhereDelegate()

    def columns(self, *columns: Column) -> Select:
        self.columns_delegate.columns(*columns)
        return self

    def count(self) -> Select:
        self.count_delegate.count()
        return self

    def distinct(self) -> Select:
        self.distinct_delegate.distinct()
        return self

    def limit(self, number: int) -> Select:
        self.limit_delegate.limit(number)
        return self

    def first(self) -> Select:
        self.limit_delegate.first()
        return self

    def response_handler(self, response):
        if self.limit_delegate._first:
            if len(response) == 0:
                raise ValueError('No results found')
            else:
                return response[0]
        else:
            return response

    def order_by(self, *columns: Column, ascending=True) -> Select:
        self.order_by_delegate.order_by(*columns, ascending=ascending)
        return self

    def output(self, **kwargs) -> Select:
        self.output_delegate.output(**kwargs)
        return self

    def where(self, where: Combinable) -> Select:
        self.where_delegate.where(where)
        return self

    ###########################################################################

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
        # JOIN
        self.check_valid_call_chain(self.columns_delegate.selected_columns)

        select_joins = self.get_joins(self.columns_delegate.selected_columns)
        where_joins = self.get_joins(self.where_delegate.get_where_columns())
        order_by_joins = self.get_joins(
            self.order_by_delegate.get_order_by_columns()
        )

        # Combine all joins, and remove duplicates
        joins: t.List[str] = list(
            OrderedDict.fromkeys(
                select_joins + where_joins + order_by_joins
            )
        )

        #######################################################################

        if len(self.columns_delegate.selected_columns) == 0:
            self.columns_delegate.selected_columns = self.table.Meta.columns

        column_names: t.List[str] = [
            c.get_full_name() for c in self.columns_delegate.selected_columns
        ]
        columns_str = ", ".join(column_names)

        #######################################################################

        select = "SELECT DISTINCT" if self.distinct else "SELECT"
        query = f'{select} {columns_str} FROM {self.table.Meta.tablename}'

        for join in joins:
            query += f" {join}"

        #######################################################################

        args: t.List[t.Any] = []

        if self.where_delegate._where:
            query += " WHERE {}"
            args.append(self.where_delegate._where.querystring)

        if self.order_by_delegate._order_by:
            query += " {}"
            args.append(self.order_by_delegate._order_by.querystring)

        if self.limit_delegate._limit:
            query += " {}"
            args.append(self.limit_delegate._limit.querystring)

        querystring = QueryString(query, *args)

        if self.count_delegate._count:
            querystring = QueryString(
                "SELECT COUNT(*) FROM ({}) AS sub_query",
                querystring
            )

        return querystring

    def __str__(self) -> str:
        return self.querystring.__str__()
