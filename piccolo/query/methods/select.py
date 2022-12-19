from __future__ import annotations

import decimal
import itertools
import typing as t
from collections import OrderedDict

from piccolo.columns import Column, Selectable
from piccolo.columns.column_types import JSON, JSONB, PrimaryKey
from piccolo.columns.m2m import M2MSelect
from piccolo.columns.readable import Readable
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AsOfDelegate,
    CallbackDelegate,
    CallbackType,
    ColumnsDelegate,
    DistinctDelegate,
    GroupByDelegate,
    LimitDelegate,
    OffsetDelegate,
    OrderByDelegate,
    OrderByRaw,
    OutputDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString
from piccolo.utils.dictionary import make_nested
from piccolo.utils.encoding import load_json
from piccolo.utils.warnings import colored_warning

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.custom_types import Combinable
    from piccolo.table import Table  # noqa


def is_numeric_column(column: Column) -> bool:
    return column.value_type in (int, decimal.Decimal, float)


class SelectRaw(Selectable):
    def __init__(self, sql: str, *args: t.Any) -> None:
        """
        Execute raw SQL in your select query.

        .. code-block:: python

            >>> await Band.select(
            ...     Band.name,
            ...     SelectRaw("log(popularity) AS log_popularity")
            ... )
            [{'name': 'Pythonistas', 'log_popularity': 3.0}]

        """
        self.querystring = QueryString(sql, *args)

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        return self.querystring.__str__()


class Avg(Selectable):
    """
    ``AVG()`` SQL function. Column type must be numeric to run the query.

    .. code-block:: python

        await Band.select(Avg(Band.popularity)).run()

        # We can use an alias. These two are equivalent:

        await Band.select(
            Avg(Band.popularity, alias="popularity_avg")
        ).run()

        await Band.select(
            Avg(Band.popularity).as_alias("popularity_avg")
        ).run()

    """

    def __init__(self, column: Column, alias: str = "avg"):
        if is_numeric_column(column):
            self.column = column
        else:
            raise ValueError("Column type must be numeric to run the query.")
        self._alias = alias

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        column_name = self.column._meta.get_full_name(with_alias=False)
        return f'AVG({column_name}) AS "{self._alias}"'


class Count(Selectable):
    """
    Used in conjunction with the ``group_by`` clause in ``Select`` queries.

    If a column is specified, the count is for non-null values in that
    column. If no column is specified, the count is for all rows, whether
    they have null values or not.

    .. code-block:: python

        await Band.select(Band.name, Count()).group_by(Band.name)

        # We can use an alias. These two are equivalent:

        await Band.select(
            Band.name, Count(alias="total")
        ).group_by(Band.name)

        await Band.select(
            Band.name,
            Count().as_alias("total")
        ).group_by(Band.name)

    """

    def __init__(
        self, column: t.Optional[Column] = None, alias: str = "count"
    ):
        self.column = column
        self._alias = alias

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        if self.column is None:
            column_name = "*"
        else:
            column_name = self.column._meta.get_full_name(with_alias=False)
        return f'COUNT({column_name}) AS "{self._alias}"'


class Max(Selectable):
    """
    ``MAX()`` SQL function.

    .. code-block:: python

        await Band.select(
            Max(Band.popularity)
        ).run()

        # We can use an alias. These two are equivalent:

        await Band.select(
            Max(Band.popularity, alias="popularity_max")
        ).run()

        await Band.select(
            Max(Band.popularity).as_alias("popularity_max")
        ).run()

    """

    def __init__(self, column: Column, alias: str = "max"):
        self.column = column
        self._alias = alias

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        column_name = self.column._meta.get_full_name(with_alias=False)
        return f'MAX({column_name}) AS "{self._alias}"'


class Min(Selectable):
    """
    ``MIN()`` SQL function.

    .. code-block:: python

        await Band.select(Min(Band.popularity)).run()

        # We can use an alias. These two are equivalent:

        await Band.select(
            Min(Band.popularity, alias="popularity_min")
        ).run()

        await Band.select(
            Min(Band.popularity).as_alias("popularity_min")
        ).run()

    """

    def __init__(self, column: Column, alias: str = "min"):
        self.column = column
        self._alias = alias

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        column_name = self.column._meta.get_full_name(with_alias=False)
        return f'MIN({column_name}) AS "{self._alias}"'


class Sum(Selectable):
    """
    ``SUM()`` SQL function. Column type must be numeric to run the query.

    .. code-block:: python

        await Band.select(
            Sum(Band.popularity)
        ).run()

        # We can use an alias. These two are equivalent:

        await Band.select(
            Sum(Band.popularity, alias="popularity_sum")
        ).run()

        await Band.select(
            Sum(Band.popularity).as_alias("popularity_sum")
        ).run()

    """

    def __init__(self, column: Column, alias: str = "sum"):
        if is_numeric_column(column):
            self.column = column
        else:
            raise ValueError("Column type must be numeric to run the query.")
        self._alias = alias

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        column_name = self.column._meta.get_full_name(with_alias=False)
        return f'SUM({column_name}) AS "{self._alias}"'


class Select(Query):
    __slots__ = (
        "columns_list",
        "exclude_secrets",
        "as_of_delegate",
        "columns_delegate",
        "distinct_delegate",
        "group_by_delegate",
        "limit_delegate",
        "offset_delegate",
        "order_by_delegate",
        "output_delegate",
        "callback_delegate",
        "where_delegate",
    )

    def __init__(
        self,
        table: t.Type[Table],
        columns_list: t.Sequence[t.Union[Selectable, str]] = None,
        exclude_secrets: bool = False,
        **kwargs,
    ):
        if columns_list is None:
            columns_list = []
        super().__init__(table, **kwargs)
        self.exclude_secrets = exclude_secrets

        self.as_of_delegate = AsOfDelegate()
        self.columns_delegate = ColumnsDelegate()
        self.distinct_delegate = DistinctDelegate()
        self.group_by_delegate = GroupByDelegate()
        self.limit_delegate = LimitDelegate()
        self.offset_delegate = OffsetDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.callback_delegate = CallbackDelegate()
        self.where_delegate = WhereDelegate()

        self.columns(*columns_list)

    def columns(self, *columns: t.Union[Selectable, str]) -> Select:
        _columns = self.table._process_column_args(*columns)
        self.columns_delegate.columns(*_columns)
        return self

    def distinct(self) -> Select:
        self.distinct_delegate.distinct()
        return self

    def group_by(self, *columns: t.Union[Column, str]) -> Select:
        _columns: t.List[Column] = [
            i
            for i in self.table._process_column_args(*columns)
            if isinstance(i, Column)
        ]
        self.group_by_delegate.group_by(*_columns)
        return self

    def as_of(self, interval: str = "-1s") -> Select:
        self.as_of_delegate.as_of(interval)
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

    async def _splice_m2m_rows(
        self,
        response: t.List[t.Dict[str, t.Any]],
        secondary_table: t.Type[Table],
        secondary_table_pk: PrimaryKey,
        m2m_name: str,
        m2m_select: M2MSelect,
        as_list: bool = False,
    ):
        row_ids = list(
            set(itertools.chain(*[row[m2m_name] for row in response]))
        )
        extra_rows = (
            (
                await secondary_table.select(
                    *m2m_select.columns,
                    secondary_table_pk.as_alias("mapping_key"),
                )
                .where(secondary_table_pk.is_in(row_ids))
                .output(load_json=m2m_select.load_json)
                .run()
            )
            if row_ids
            else []
        )
        if as_list:
            column_name = m2m_select.columns[0]._meta.name
            extra_rows_map = {
                row["mapping_key"]: row[column_name] for row in extra_rows
            }
        else:
            extra_rows_map = {
                row["mapping_key"]: {
                    key: value
                    for key, value in row.items()
                    if key != "mapping_key"
                }
                for row in extra_rows
            }
        for row in response:
            row[m2m_name] = [extra_rows_map.get(i) for i in row[m2m_name]]
        return response

    async def response_handler(self, response):
        m2m_selects = [
            i
            for i in self.columns_delegate.selected_columns
            if isinstance(i, M2MSelect)
        ]
        for m2m_select in m2m_selects:
            m2m_name = m2m_select.m2m._meta.name
            secondary_table = m2m_select.m2m._meta.secondary_table
            secondary_table_pk = secondary_table._meta.primary_key

            if self.engine_type == "sqlite":
                # With M2M queries in SQLite, we always get the value back as a
                # list of strings, so we need to do some type conversion.
                value_type = (
                    m2m_select.columns[0].__class__.value_type
                    if m2m_select.as_list and m2m_select.serialisation_safe
                    else secondary_table_pk.value_type
                )
                try:
                    for row in response:
                        data = row[m2m_name]
                        row[m2m_name] = (
                            [value_type(i) for i in row[m2m_name]]
                            if data
                            else []
                        )
                except ValueError:
                    colored_warning(
                        "Unable to do type conversion for the "
                        f"{m2m_name} relation"
                    )

                # If the user requested a single column, we just return that
                # from the database. Otherwise we request the primary key
                # value, so we can fetch the rest of the data in a subsequent
                # SQL query - see below.
                if m2m_select.as_list:
                    if m2m_select.serialisation_safe:
                        pass
                    else:
                        response = await self._splice_m2m_rows(
                            response,
                            secondary_table,
                            secondary_table_pk,
                            m2m_name,
                            m2m_select,
                            as_list=True,
                        )
                else:
                    if (
                        len(m2m_select.columns) == 1
                        and m2m_select.serialisation_safe
                    ):
                        column_name = m2m_select.columns[0]._meta.name
                        for row in response:
                            row[m2m_name] = [
                                {column_name: i} for i in row[m2m_name]
                            ]
                    else:
                        response = await self._splice_m2m_rows(
                            response,
                            secondary_table,
                            secondary_table_pk,
                            m2m_name,
                            m2m_select,
                        )

            elif self.engine_type in ("postgres", "cockroach"):
                if m2m_select.as_list:
                    # We get the data back as an array, and can just return it
                    # unless it's JSON.
                    if (
                        type(m2m_select.columns[0]) in (JSON, JSONB)
                        and m2m_select.load_json
                    ):
                        for row in response:
                            data = row[m2m_name]
                            row[m2m_name] = [load_json(i) for i in data]
                elif m2m_select.serialisation_safe:
                    # If the columns requested can be safely serialised, they
                    # are returned as a JSON string, so we need to deserialise
                    # it.
                    for row in response:
                        data = row[m2m_name]
                        row[m2m_name] = load_json(data) if data else []
                else:
                    # If the data can't be safely serialised as JSON, we get
                    # back an array of primary key values, and need to
                    # splice in the correct values using Python.
                    response = await self._splice_m2m_rows(
                        response,
                        secondary_table,
                        secondary_table_pk,
                        m2m_name,
                        m2m_select,
                    )

        #######################################################################

        # If no columns were specified, it's a select *, so we know that
        # no columns were selected from related tables.
        was_select_star = len(self.columns_delegate.selected_columns) == 0

        if self.limit_delegate._first:
            if len(response) == 0:
                return None

            if self.output_delegate._output.nested and not was_select_star:
                return make_nested(response[0])
            else:
                return response[0]
        elif self.output_delegate._output.nested and not was_select_star:
            return [make_nested(i) for i in response]
        else:
            return response

    def order_by(
        self, *columns: t.Union[Column, str, OrderByRaw], ascending=True
    ) -> Select:
        """
        :param columns:
            Either a :class:`piccolo.columns.base.Column` instance, a string
            representing a column name, or :class:`piccolo.query.OrderByRaw`
            which allows you for complex use cases like
            ``OrderByRaw('random()')``.
        """
        _columns: t.List[t.Union[Column, OrderByRaw]] = []
        for column in columns:
            if isinstance(column, str):
                _columns.append(self.table._meta.get_column_by_name(column))
            else:
                _columns.append(column)

        self.order_by_delegate.order_by(*_columns, ascending=ascending)
        return self

    def output(
        self,
        as_list: bool = False,
        as_json: bool = False,
        load_json: bool = False,
        nested: bool = False,
    ) -> Select:
        self.output_delegate.output(
            as_list=as_list,
            as_json=as_json,
            load_json=load_json,
            nested=nested,
        )
        return self

    def callback(
        self,
        callbacks: t.Union[t.Callable, t.List[t.Callable]],
        *,
        on: CallbackType = CallbackType.success,
    ) -> Select:
        self.callback_delegate.callback(callbacks, on=on)
        return self

    def where(self, *where: Combinable) -> Select:
        self.where_delegate.where(*where)
        return self

    async def batch(
        self,
        batch_size: t.Optional[int] = None,
        node: t.Optional[str] = None,
        **kwargs,
    ) -> Batch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        if node:
            kwargs.update(node=node)
        return await self.table._meta.db.batch(self, **kwargs)

    ###########################################################################

    def _get_joins(self, columns: t.Sequence[Selectable]) -> t.List[str]:
        """
        A call chain is a sequence of foreign keys representing joins which
        need to be made to retrieve a column in another table.
        """
        joins: t.List[str] = []

        readables: t.List[Readable] = [
            i for i in columns if isinstance(i, Readable)
        ]

        columns = list(columns)
        for readable in readables:
            columns += readable.columns

        for column in columns:
            if not isinstance(column, Column):
                continue

            _joins: t.List[str] = []
            for index, key in enumerate(column._meta.call_chain, 0):
                table_alias = "$".join(
                    f"{_key._meta.table._meta.tablename}${_key._meta.name}"
                    for _key in column._meta.call_chain[: index + 1]
                )

                key._meta.table_alias = table_alias

                if index > 0:
                    left_tablename = column._meta.call_chain[
                        index - 1
                    ]._meta.table_alias
                else:
                    left_tablename = key._meta.table._meta.tablename

                right_tablename = (
                    key._foreign_key_meta.resolved_references._meta.tablename
                )

                pk_name = column._meta.call_chain[
                    index
                ]._foreign_key_meta.resolved_target_column._meta.name

                _joins.append(
                    f'LEFT JOIN "{right_tablename}" "{table_alias}"'
                    " ON "
                    f'("{left_tablename}"."{key._meta.name}" = "{table_alias}"."{pk_name}")'  # noqa: E501
                )

            joins.extend(_joins)

        # Remove duplicates
        return list(OrderedDict.fromkeys(joins))

    def _check_valid_call_chain(self, keys: t.Sequence[Selectable]) -> bool:
        for column in keys:
            if not isinstance(column, Column):
                continue
            if column._meta.call_chain and len(column._meta.call_chain) > 10:
                # Make sure the call_chain isn't too large to discourage
                # very inefficient queries.
                raise Exception(
                    "Joining more than 10 tables isn't supported - "
                    "please restructure your query."
                )
        return True

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
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

        select = (
            "SELECT DISTINCT" if self.distinct_delegate._distinct else "SELECT"
        )
        query = f"{select} {columns_str} FROM {self.table._meta.tablename}"

        for join in joins:
            query += f" {join}"

        #######################################################################

        args: t.List[t.Any] = []

        if self.as_of_delegate._as_of:
            query += "{}"
            args.append(self.as_of_delegate._as_of.querystring)

        if self.where_delegate._where:
            query += " WHERE {}"
            args.append(self.where_delegate._where.querystring)

        if self.group_by_delegate._group_by:
            query += "{}"
            args.append(self.group_by_delegate._group_by.querystring)

        if self.order_by_delegate._order_by.order_by_items:
            query += "{}"
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
            query += "{}"
            args.append(self.limit_delegate._limit.querystring)

        if self.offset_delegate._offset:
            query += "{}"
            args.append(self.offset_delegate._offset.querystring)

        querystring = QueryString(query, *args)

        return [querystring]
