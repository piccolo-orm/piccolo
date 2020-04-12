from __future__ import annotations
from collections import OrderedDict
import typing as t

from piccolo.columns import Column, Selectable
from piccolo.columns.readable import Readable
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    ColumnsDelegate,
    DistinctDelegate,
    LimitDelegate,
    OffsetDelegate,
    OrderByDelegate,
    OutputDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from piccolo.table import Table  # noqa
    from piccolo.custom_types import Combinable


class Select(Query):

    __slots__ = (
        "columns_list",
        "exclude_secrets",
        "columns_delegate",
        "distinct_delegate",
        "limit_delegate",
        "offset_delegate",
        "order_by_delegate",
        "output_delegate",
        "where_delegate",
    )

    def __init__(
        self,
        table: t.Type[Table],
        columns_list: t.Sequence[Selectable] = [],
        exclude_secrets: bool = False,
    ):
        super().__init__(table)
        self.exclude_secrets = exclude_secrets

        self.columns_delegate = ColumnsDelegate()
        self.distinct_delegate = DistinctDelegate()
        self.limit_delegate = LimitDelegate()
        self.offset_delegate = OffsetDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.where_delegate = WhereDelegate()

        self.columns(*columns_list)

    def columns(self, *columns: t.Union[Column, str]) -> Select:
        _columns = self.table._process_column_args(*columns)
        self.columns_delegate.columns(*_columns)
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

    def offset(self, number: int) -> Select:
        self.offset_delegate.offset(number)
        return self

    async def response_handler(self, response):
        if self.limit_delegate._first:
            if len(response) == 0:
                return None
            else:
                return response[0]
        else:
            return response

    def order_by(self, *columns: Column, ascending=True) -> Select:
        columns = self.table._process_column_args(*columns)
        self.order_by_delegate.order_by(*columns, ascending=ascending)
        return self

    def output(self, **kwargs) -> Select:
        self.output_delegate.output(**kwargs)
        return self

    def where(self, where: Combinable) -> Select:
        self.where_delegate.where(where)
        return self

    async def batch(
        self, batch_size: t.Optional[int] = None, **kwargs
    ) -> Batch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        return await self.table._meta.db.batch(self, **kwargs)

    ###########################################################################

    def _get_joins(self, columns: t.Sequence[Selectable]) -> t.List[str]:
        """
        A call chain is a sequence of foreign keys representing joins which
        need to be made to retrieve a column in another table.
        """
        joins: t.List[str] = []

        readables = [i for i in columns if isinstance(i, Readable)]
        for readable in readables:
            columns += readable.columns

        for column in columns:
            if not isinstance(column, Column):
                continue

            _joins: t.List[str] = []
            for index, key in enumerate(column._meta.call_chain, 0):
                table_alias = "$".join(
                    [
                        f"{_key._meta.table._meta.tablename}${_key._meta.name}"
                        for _key in column._meta.call_chain[: index + 1]
                    ]
                )
                key._meta.table_alias = table_alias

                if index > 0:
                    left_tablename = column._meta.call_chain[
                        index - 1
                    ]._meta.table_alias
                else:
                    left_tablename = key._meta.table._meta.tablename

                right_tablename = (
                    key._foreign_key_meta.references._meta.tablename
                )

                _joins.append(
                    f"LEFT JOIN {right_tablename} {table_alias}"
                    " ON "
                    f"({left_tablename}.{key._meta.name} = {table_alias}.id)"
                )

            joins.extend(_joins)

        # Remove duplicates
        return list(OrderedDict.fromkeys(joins))

    def _check_valid_call_chain(self, keys: t.Sequence[Selectable]) -> bool:
        for column in keys:
            if not isinstance(column, Column):
                continue
            if column._meta.call_chain:
                # Make sure the call_chain isn't too large to discourage
                # very inefficient queries.

                if len(column._meta.call_chain) > 10:
                    raise Exception(
                        "Joining more than 10 tables isn't supported - "
                        "please restructure your query."
                    )
        return True

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        # JOIN
        self._check_valid_call_chain(self.columns_delegate.selected_columns)

        select_joins = self._get_joins(self.columns_delegate.selected_columns)
        where_joins = self._get_joins(self.where_delegate.get_where_columns())
        order_by_joins = self._get_joins(
            self.order_by_delegate.get_order_by_columns()
        )

        # Combine all joins, and remove duplicates
        joins: t.List[str] = list(
            OrderedDict.fromkeys(select_joins + where_joins + order_by_joins)
        )

        #######################################################################

        # If no columns have been specified for selection, select all columns
        # on the table:
        if len(self.columns_delegate.selected_columns) == 0:
            self.columns_delegate.selected_columns = self.table._meta.columns

        # If secret fields need to be omitted, remove them from the list.
        if self.exclude_secrets:
            self.columns_delegate.remove_secret_columns()

        engine_type = self.table._meta.db.engine_type

        select_strings: t.List[str] = [
            c.get_select_string(engine_type=engine_type)
            for c in self.columns_delegate.selected_columns
        ]
        columns_str = ", ".join(select_strings)

        #######################################################################

        select = "SELECT DISTINCT" if self.distinct else "SELECT"
        query = f"{select} {columns_str} FROM {self.table._meta.tablename}"

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

        if (
            engine_type == "sqlite"
            and self.offset_delegate._offset
            and not self.limit_delegate._limit
        ):
            raise ValueError(
                "A limit clause must be provided when doing an offset with "
                "SQLite."
            )

        if self.limit_delegate._limit:
            query += " {}"
            args.append(self.limit_delegate._limit.querystring)

        if self.offset_delegate._offset:
            query += " {}"
            args.append(self.offset_delegate._offset.querystring)

        querystring = QueryString(query, *args)

        return [querystring]
