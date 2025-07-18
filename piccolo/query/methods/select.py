from __future__ import annotations

import itertools
from collections import OrderedDict
from collections.abc import Callable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Optional,
    TypeVar,
    Union,
    overload,
)

from piccolo.columns import Column, Selectable
from piccolo.columns.column_types import JSON, JSONB
from piccolo.columns.m2m import M2MSelect
from piccolo.columns.readable import Readable
from piccolo.custom_types import TableInstance
from piccolo.engine.base import BaseBatch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AsOfDelegate,
    CallbackDelegate,
    CallbackType,
    ColumnsDelegate,
    DistinctDelegate,
    GroupByDelegate,
    LimitDelegate,
    LockRowsDelegate,
    LockStrength,
    OffsetDelegate,
    OrderByDelegate,
    OrderByRaw,
    OutputDelegate,
    WhereDelegate,
)
from piccolo.query.proxy import Proxy
from piccolo.querystring import QueryString
from piccolo.utils.dictionary import make_nested
from piccolo.utils.encoding import dump_json, load_json
from piccolo.utils.warnings import colored_warning

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.custom_types import Combinable
    from piccolo.table import Table  # noqa

# Here to avoid breaking changes - will be removed in the future.
from piccolo.query.functions.aggregate import (  # noqa: F401
    Avg,
    Count,
    Max,
    Min,
    Sum,
)


class SelectRaw(Selectable):
    def __init__(self, sql: str, *args: Any) -> None:
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
    ) -> QueryString:
        return self.querystring


OptionalDict = Optional[dict[str, Any]]


class First(Proxy["Select", OptionalDict]):
    """
    This is for static typing purposes.
    """

    def __init__(self, query: Select):
        self.query = query

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
    ) -> OptionalDict:
        rows = await self.query.run(
            node=node, in_pool=in_pool, use_callbacks=False
        )
        results = rows[0] if rows else None

        modified_response = await self.query.callback_delegate.invoke(
            results=results, kind=CallbackType.success
        )
        return modified_response


class SelectList(Proxy["Select", list]):
    """
    This is for static typing purposes.
    """

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
    ) -> list:
        rows = await self.query.run(
            node=node, in_pool=in_pool, use_callbacks=False
        )

        if len(rows) == 0:
            response = []
        else:
            if len(rows[0].keys()) != 1:
                raise ValueError("Each row returned more than one value")

            response = list(itertools.chain(*[j.values() for j in rows]))

        modified_response = await self.query.callback_delegate.invoke(
            results=response, kind=CallbackType.success
        )
        return modified_response


class SelectJSON(Proxy["Select", str]):
    """
    This is for static typing purposes.
    """

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
    ) -> str:
        rows = await self.query.run(node=node, in_pool=in_pool)
        return dump_json(rows)


class Select(Query[TableInstance, list[dict[str, Any]]]):
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
        "lock_rows_delegate",
    )

    def __init__(
        self,
        table: type[TableInstance],
        columns_list: Optional[Sequence[Union[Selectable, str]]] = None,
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
        self.lock_rows_delegate = LockRowsDelegate()

        self.columns(*columns_list)

    def columns(self: Self, *columns: Union[Selectable, str]) -> Self:
        _columns = self.table._process_column_args(*columns)
        self.columns_delegate.columns(*_columns)
        return self

    def distinct(self: Self, *, on: Optional[Sequence[Column]] = None) -> Self:
        if on is not None and self.engine_type == "sqlite":
            raise NotImplementedError("SQLite doesn't support DISTINCT ON")

        self.distinct_delegate.distinct(enabled=True, on=on)
        return self

    def group_by(self: Self, *columns: Union[Column, str]) -> Self:
        _columns: list[Column] = [
            i
            for i in self.table._process_column_args(*columns)
            if isinstance(i, Column)
        ]
        self.group_by_delegate.group_by(*_columns)
        return self

    def as_of(self: Self, interval: str = "-1s") -> Self:
        if self.engine_type != "cockroach":
            raise NotImplementedError("Only CockroachDB supports AS OF")

        self.as_of_delegate.as_of(interval)
        return self

    def limit(self: Self, number: int) -> Self:
        self.limit_delegate.limit(number)
        return self

    def first(self) -> First:
        self.limit_delegate.limit(1)
        return First(query=self)

    def offset(self: Self, number: int) -> Self:
        self.offset_delegate.offset(number)
        return self

    def lock_rows(
        self: Self,
        lock_strength: Union[
            LockStrength,
            Literal[
                "UPDATE",
                "NO KEY UPDATE",
                "KEY SHARE",
                "SHARE",
            ],
        ] = LockStrength.update,
        nowait: bool = False,
        skip_locked: bool = False,
        of: tuple[type[Table], ...] = (),
    ) -> Self:
        self.lock_rows_delegate.lock_rows(
            lock_strength, nowait, skip_locked, of
        )
        return self

    async def _splice_m2m_rows(
        self,
        response: list[dict[str, Any]],
        secondary_table: type[Table],
        secondary_table_pk: Column,
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

        if self.output_delegate._output.nested and not was_select_star:
            return [make_nested(i) for i in response]
        else:
            return response

    def order_by(
        self: Self, *columns: Union[Column, str, OrderByRaw], ascending=True
    ) -> Self:
        """
        :param columns:
            Either a :class:`piccolo.columns.base.Column` instance, a string
            representing a column name, or :class:`piccolo.query.OrderByRaw`
            which allows you for complex use cases like
            ``OrderByRaw('random()')``.
        """
        _columns: list[Union[Column, OrderByRaw]] = []
        for column in columns:
            if isinstance(column, str):
                _columns.append(self.table._meta.get_column_by_name(column))
            else:
                _columns.append(column)

        self.order_by_delegate.order_by(*_columns, ascending=ascending)
        return self

    @overload
    def output(self: Self, *, as_list: bool) -> SelectList:  # type: ignore
        ...

    @overload
    def output(self: Self, *, as_json: bool) -> SelectJSON:  # type: ignore
        ...

    @overload
    def output(self: Self, *, load_json: bool) -> Self: ...

    @overload
    def output(self: Self, *, load_json: bool, as_list: bool) -> SelectJSON:  # type: ignore  # noqa: E501
        ...

    @overload
    def output(self: Self, *, load_json: bool, nested: bool) -> Self: ...

    @overload
    def output(self: Self, *, nested: bool) -> Self: ...

    def output(
        self: Self,
        *,
        as_list: bool = False,
        as_json: bool = False,
        load_json: bool = False,
        nested: bool = False,
    ) -> Union[Self, SelectJSON, SelectList]:
        self.output_delegate.output(
            as_list=as_list,
            as_json=as_json,
            load_json=load_json,
            nested=nested,
        )
        if as_list:
            return SelectList(query=self)
        elif as_json:
            return SelectJSON(query=self)

        return self

    def callback(
        self: Self,
        callbacks: Union[Callable, list[Callable]],
        *,
        on: CallbackType = CallbackType.success,
    ) -> Self:
        self.callback_delegate.callback(callbacks, on=on)
        return self

    def where(self: Self, *where: Union[Combinable, QueryString]) -> Self:
        self.where_delegate.where(*where)
        return self

    async def batch(
        self,
        batch_size: Optional[int] = None,
        node: Optional[str] = None,
        **kwargs,
    ) -> BaseBatch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        if node:
            kwargs.update(node=node)
        return await self.table._meta.db.batch(self, **kwargs)

    ###########################################################################

    def _get_joins(self, columns: Sequence[Selectable]) -> list[str]:
        """
        A call chain is a sequence of foreign keys representing joins which
        need to be made to retrieve a column in another table.
        """
        joins: list[str] = []

        readables: list[Readable] = [
            i for i in columns if isinstance(i, Readable)
        ]

        columns = list(columns)
        for readable in readables:
            columns += readable.columns

        querystrings: list[QueryString] = [
            i for i in columns if isinstance(i, QueryString)
        ]
        for querystring in querystrings:
            if querystring_columns := getattr(querystring, "columns", []):
                columns += querystring_columns

        for column in columns:
            if not isinstance(column, Column):
                continue

            _joins: list[str] = []
            for index, key in enumerate(column._meta.call_chain, 0):
                table_alias = key.table_alias

                if index > 0:
                    left_tablename = column._meta.call_chain[
                        index - 1
                    ].table_alias
                else:
                    left_tablename = (
                        key._meta.table._meta.get_formatted_tablename()
                    )  # noqa: E501

                right_tablename = (
                    key._foreign_key_meta.resolved_references._meta.get_formatted_tablename()  # noqa: E501
                )

                pk_name = column._meta.call_chain[
                    index
                ]._foreign_key_meta.resolved_target_column._meta.name

                _joins.append(
                    f'LEFT JOIN {right_tablename} "{table_alias}"'
                    " ON "
                    f'({left_tablename}."{key._meta.db_column_name}" = "{table_alias}"."{pk_name}")'  # noqa: E501
                )

            joins.extend(_joins)

        # Remove duplicates
        return list(OrderedDict.fromkeys(joins))

    def _check_valid_call_chain(self, keys: Sequence[Selectable]) -> bool:
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
    def default_querystrings(self) -> Sequence[QueryString]:
        # JOIN
        self._check_valid_call_chain(self.columns_delegate.selected_columns)

        select_joins = self._get_joins(self.columns_delegate.selected_columns)
        where_joins = self._get_joins(self.where_delegate.get_where_columns())
        order_by_joins = self._get_joins(
            self.order_by_delegate.get_order_by_columns()
        )

        # Combine all joins, and remove duplicates
        joins: list[str] = list(
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

        select_strings: list[QueryString] = [
            c.get_select_string(engine_type=engine_type)
            for c in self.columns_delegate.selected_columns
        ]

        #######################################################################

        args: list[Any] = []

        query = "SELECT"

        distinct = self.distinct_delegate._distinct
        if distinct.on:
            distinct.validate_on(self.order_by_delegate._order_by)
        query += "{}"
        args.append(distinct.querystring)

        columns_str = ", ".join("{}" for _ in select_strings)
        query += f" {columns_str} FROM {self.table._meta.get_formatted_tablename()}"  # noqa: E501
        args.extend(select_strings)

        for join in joins:
            query += f" {join}"

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

        if self.lock_rows_delegate._lock_rows:
            if engine_type == "sqlite":
                raise NotImplementedError(
                    "SQLite doesn't support row locking e.g. SELECT ... FOR "
                    "UPDATE"
                )

            query += "{}"
            args.append(self.lock_rows_delegate._lock_rows.querystring)

        querystring = QueryString(query, *args)

        return [querystring]

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
        use_callbacks: bool = True,
        **kwargs,
    ) -> list[dict[str, Any]]:
        results = await super().run(node=node, in_pool=in_pool)
        if use_callbacks:
            return await self.callback_delegate.invoke(
                results, kind=CallbackType.success
            )
        else:
            return results


Self = TypeVar("Self", bound=Select)
