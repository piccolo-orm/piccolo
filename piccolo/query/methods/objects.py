from __future__ import annotations

from collections.abc import Callable, Generator, Sequence
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
    cast,
)

from piccolo.columns.column_types import ForeignKey, ReferencedTable
from piccolo.columns.combination import And, Where
from piccolo.custom_types import Combinable, TableInstance
from piccolo.engine.base import BaseBatch
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import (
    AsOfDelegate,
    CallbackDelegate,
    CallbackType,
    LimitDelegate,
    LockRowsDelegate,
    LockStrength,
    OffsetDelegate,
    OrderByDelegate,
    OrderByRaw,
    OutputDelegate,
    PrefetchDelegate,
    WhereDelegate,
)
from piccolo.query.proxy import Proxy
from piccolo.querystring import QueryString
from piccolo.utils.dictionary import make_nested
from piccolo.utils.sync import run_sync

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


###############################################################################


class GetOrCreate(
    Proxy["Objects[TableInstance]", TableInstance], Generic[TableInstance]
):
    def __init__(
        self,
        query: Objects[TableInstance],
        table_class: type[TableInstance],
        where: Combinable,
        defaults: dict[Column, Any],
    ):
        self.query = query
        self.table_class = table_class
        self.where = where
        self.defaults = defaults

    async def run(
        self, node: Optional[str] = None, in_pool: bool = True
    ) -> TableInstance:
        """
        :raises ValueError:
            If more than one matching row is found.

        """
        instance = await self.query.get(self.where).run(
            node=node, in_pool=in_pool
        )
        if instance:
            instance._was_created = False
            return instance

        data = {**self.defaults}

        # If it's a complex `where`, there can be several column values to
        # extract e.g. (Band.name == 'Pythonistas') & (Band.popularity == 1000)
        if isinstance(self.where, Where):
            data[self.where.column] = self.where.value
        elif isinstance(self.where, And):
            for column, value in self.where.get_column_values().items():
                if len(column._meta.call_chain) == 0:
                    # Make sure we only set the value if the column belongs
                    # to this table.
                    data[column] = value

        instance = self.table_class(_data=data)

        await instance.save().run(node=node, in_pool=in_pool)

        # If the user wants us to prefetch related objects, for example:
        #
        # await Band.objects(Band.manager).get_or_create(
        #   (Band.name == 'Pythonistas') & (Band.manager == 1)
        # )
        #
        # Then we need to fetch the related objects.
        # See https://github.com/piccolo-orm/piccolo/issues/597
        prefetch = self.query.prefetch_delegate.fk_columns
        if prefetch:
            table = instance.__class__
            primary_key = table._meta.primary_key
            instance = (
                await table.objects(*prefetch)
                .get(primary_key == getattr(instance, primary_key._meta.name))
                .run()
            )

        instance = cast(TableInstance, instance)
        instance._was_created = True
        return instance


class Get(
    Proxy["First[TableInstance]", Optional[TableInstance]],
    Generic[TableInstance],
):
    pass


class First(
    Proxy["Objects[TableInstance]", Optional[TableInstance]],
    Generic[TableInstance],
):
    async def run(
        self, node: Optional[str] = None, in_pool: bool = True
    ) -> Optional[TableInstance]:
        objects = await self.query.run(
            node=node, in_pool=in_pool, use_callbacks=False
        )

        results = objects[0] if objects else None

        modified_response: Optional[TableInstance] = (
            await self.query.callback_delegate.invoke(
                results=results, kind=CallbackType.success
            )
        )
        return modified_response


class Create(Generic[TableInstance]):
    """
    This is provided as a simple convenience. Rather than running::

        band = Band(name='Pythonistas')
        await band.save()

    We can instead do it in a single line::

        band = Band.objects().create(name='Pythonistas')

    """

    def __init__(
        self,
        table_class: type[TableInstance],
        columns: dict[str, Any],
    ):
        self.table_class = table_class
        self.columns = columns

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
    ) -> TableInstance:
        instance = self.table_class(**self.columns)
        await instance.save().run(node=node, in_pool=in_pool)
        return instance

    def __await__(self) -> Generator[None, None, TableInstance]:
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self, *args, **kwargs) -> TableInstance:
        return run_sync(self.run(*args, **kwargs))


class UpdateSelf:

    def __init__(
        self,
        row: Table,
        values: dict[Union[Column, str], Any],
    ):
        self.row = row
        self.values = values

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
    ) -> None:
        if not self.row._exists_in_db:
            raise ValueError("This row doesn't exist in the database.")

        TableClass = self.row.__class__

        primary_key = TableClass._meta.primary_key
        primary_key_value = getattr(self.row, primary_key._meta.name)

        if primary_key_value is None:
            raise ValueError("The primary key is None")

        columns = [
            TableClass._meta.get_column_by_name(i) if isinstance(i, str) else i
            for i in self.values.keys()
        ]

        response = (
            await TableClass.update(self.values)
            .where(primary_key == primary_key_value)
            .returning(*columns)
            .run(
                node=node,
                in_pool=in_pool,
            )
        )

        for key, value in response[0].items():
            setattr(self.row, key, value)

    def __await__(self) -> Generator[None, None, None]:
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self, *args, **kwargs) -> None:
        return run_sync(self.run(*args, **kwargs))


class GetRelated(Generic[ReferencedTable]):

    def __init__(self, row: Table, foreign_key: ForeignKey[ReferencedTable]):
        self.row = row
        self.foreign_key = foreign_key

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
    ) -> Optional[ReferencedTable]:
        if not self.row._exists_in_db:
            raise ValueError("The object doesn't exist in the database.")

        root_table = self.row.__class__

        data = (
            await root_table.select(
                *[
                    i.as_alias(i._meta.name)
                    for i in self.foreign_key.all_columns()
                ]
            )
            .where(
                root_table._meta.primary_key
                == getattr(self.row, root_table._meta.primary_key._meta.name)
            )
            .first()
            .run(node=node, in_pool=in_pool)
        )

        # Make sure that some values were returned:
        if data is None or not any(data.values()):
            return None

        references = cast(
            type[ReferencedTable],
            self.foreign_key._foreign_key_meta.resolved_references,
        )

        referenced_object = references(**data)
        referenced_object._exists_in_db = True
        return referenced_object

    def __await__(
        self,
    ) -> Generator[None, None, Optional[ReferencedTable]]:
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self, *args, **kwargs) -> Optional[ReferencedTable]:
        return run_sync(self.run(*args, **kwargs))


###############################################################################


@dataclass
class _ObjectsConditionDelegates:
    where: WhereDelegate = field(default_factory=WhereDelegate)


@dataclass
class _ObjectsSortDelegates:
    order_by: OrderByDelegate = field(default_factory=OrderByDelegate)


@dataclass
class _ObjectsPaginationDelegates:
    limit: LimitDelegate = field(default_factory=LimitDelegate)
    offset: OffsetDelegate = field(default_factory=OffsetDelegate)


@dataclass
class _ObjectsOutputDelegates:
    output: OutputDelegate = field(default_factory=OutputDelegate)
    callback: CallbackDelegate = field(default_factory=CallbackDelegate)


@dataclass
class _ObjectsMiscDelegates:
    as_of: AsOfDelegate = field(default_factory=AsOfDelegate)
    lock_rows: LockRowsDelegate = field(default_factory=LockRowsDelegate)
    prefetch: PrefetchDelegate = field(default_factory=PrefetchDelegate)


###############################################################################


class Objects(
    Query[TableInstance, list[TableInstance]], Generic[TableInstance]
):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    __slots__ = (
        "_condition",
        "_sort",
        "_pagination",
        "_output",
        "_misc",
    )

    def __init__(
        self,
        table: type[TableInstance],
        prefetch: Sequence[Union[ForeignKey, list[ForeignKey]]] = (),
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self._condition = _ObjectsConditionDelegates()
        self._sort = _ObjectsSortDelegates()
        self._pagination = _ObjectsPaginationDelegates()
        self._output = _ObjectsOutputDelegates()
        self._output.output._output.as_objects = True
        self._misc = _ObjectsMiscDelegates()
        self.prefetch(*prefetch)

    ###########################################################################
    # Backward-compatible properties for delegates

    @property
    def as_of_delegate(self) -> AsOfDelegate:
        return self._misc.as_of

    @as_of_delegate.setter
    def as_of_delegate(self, value: AsOfDelegate) -> None:
        self._misc.as_of = value

    @property
    def limit_delegate(self) -> LimitDelegate:
        return self._pagination.limit

    @limit_delegate.setter
    def limit_delegate(self, value: LimitDelegate) -> None:
        self._pagination.limit = value

    @property
    def offset_delegate(self) -> OffsetDelegate:
        return self._pagination.offset

    @offset_delegate.setter
    def offset_delegate(self, value: OffsetDelegate) -> None:
        self._pagination.offset = value

    @property
    def order_by_delegate(self) -> OrderByDelegate:
        return self._sort.order_by

    @order_by_delegate.setter
    def order_by_delegate(self, value: OrderByDelegate) -> None:
        self._sort.order_by = value

    @property
    def output_delegate(self) -> OutputDelegate:
        return self._output.output

    @output_delegate.setter
    def output_delegate(self, value: OutputDelegate) -> None:
        self._output.output = value

    @property
    def callback_delegate(self) -> CallbackDelegate:
        return self._output.callback

    @callback_delegate.setter
    def callback_delegate(self, value: CallbackDelegate) -> None:
        self._output.callback = value

    @property
    def prefetch_delegate(self) -> PrefetchDelegate:
        return self._misc.prefetch

    @prefetch_delegate.setter
    def prefetch_delegate(self, value: PrefetchDelegate) -> None:
        self._misc.prefetch = value

    @property
    def where_delegate(self) -> WhereDelegate:
        return self._condition.where

    @where_delegate.setter
    def where_delegate(self, value: WhereDelegate) -> None:
        self._condition.where = value

    @property
    def lock_rows_delegate(self) -> LockRowsDelegate:
        return self._misc.lock_rows

    @lock_rows_delegate.setter
    def lock_rows_delegate(self, value: LockRowsDelegate) -> None:
        self._misc.lock_rows = value

    ###########################################################################

    def output(self: Self, load_json: bool = False) -> Self:
        self.output_delegate.output(
            as_list=False, as_json=False, load_json=load_json
        )
        return self

    def callback(
        self: Self,
        callbacks: Union[Callable, list[Callable]],
        *,
        on: CallbackType = CallbackType.success,
    ) -> Self:
        self.callback_delegate.callback(callbacks, on=on)
        return self

    def as_of(self, interval: str = "-1s") -> Objects:
        if self.engine_type != "cockroach":
            raise NotImplementedError("Only CockroachDB supports AS OF")
        self.as_of_delegate.as_of(interval)
        return self

    def limit(self: Self, number: int) -> Self:
        self.limit_delegate.limit(number)
        return self

    def prefetch(
        self: Self, *fk_columns: Union[ForeignKey, list[ForeignKey]]
    ) -> Self:
        self.prefetch_delegate.prefetch(*fk_columns)
        return self

    def offset(self: Self, number: int) -> Self:
        self.offset_delegate.offset(number)
        return self

    def order_by(
        self: Self, *columns: Union[Column, str, OrderByRaw], ascending=True
    ) -> Self:
        _columns: list[Union[Column, OrderByRaw]] = []
        for column in columns:
            if isinstance(column, str):
                _columns.append(self.table._meta.get_column_by_name(column))
            else:
                _columns.append(column)

        self.order_by_delegate.order_by(*_columns, ascending=ascending)
        return self

    def where(self: Self, *where: Union[Combinable, QueryString]) -> Self:
        self.where_delegate.where(*where)
        return self

    ###########################################################################

    def first(self) -> First[TableInstance]:
        self.limit_delegate.limit(1)
        return First[TableInstance](query=self)

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

    def get(self, where: Combinable) -> Get[TableInstance]:
        self.where_delegate.where(where)
        self.limit_delegate.limit(1)
        return Get[TableInstance](query=First[TableInstance](query=self))

    def get_or_create(
        self,
        where: Combinable,
        defaults: Optional[dict[Column, Any]] = None,
    ) -> GetOrCreate[TableInstance]:
        if defaults is None:
            defaults = {}
        return GetOrCreate[TableInstance](
            query=self, table_class=self.table, where=where, defaults=defaults
        )

    def create(self, **columns: Any) -> Create[TableInstance]:
        return Create[TableInstance](table_class=self.table, columns=columns)

    ###########################################################################

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

    async def response_handler(self, response):
        if self.output_delegate._output.nested:
            return [make_nested(i) for i in response]
        else:
            return response

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        select = Select(table=self.table)

        for attr in (
            "as_of_delegate",
            "limit_delegate",
            "where_delegate",
            "offset_delegate",
            "output_delegate",
            "order_by_delegate",
            "lock_rows_delegate",
        ):
            setattr(select, attr, getattr(self, attr))

        if self.prefetch_delegate.fk_columns:
            select.columns(*self.table.all_columns())
            for fk in self.prefetch_delegate.fk_columns:
                if isinstance(fk, ForeignKey):
                    select.columns(*fk.all_columns())
                else:
                    raise ValueError(f"{fk} doesn't seem to be a ForeignKey.")

                # Make sure that all intermediate objects are fully loaded.
                for parent_fk in fk._meta.call_chain:
                    select.columns(*parent_fk.all_columns())

            select.output_delegate.output(nested=True)

        return select.querystrings

    ###########################################################################

    async def run(
        self,
        node: Optional[str] = None,
        in_pool: bool = True,
        use_callbacks: bool = True,
    ) -> list[TableInstance]:
        results = await super().run(node=node, in_pool=in_pool)

        if use_callbacks:
            # With callbacks, the user can return any data that they want.
            # Assume that most of the time they will still return a list of
            # Table instances.
            modified: list[TableInstance] = (
                await self.callback_delegate.invoke(
                    results, kind=CallbackType.success
                )
            )
            return modified
        else:
            return results

    def __await__(
        self,
    ) -> Generator[None, None, list[TableInstance]]:
        return super().__await__()


Self = TypeVar("Self", bound=Objects)
