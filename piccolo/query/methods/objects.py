from __future__ import annotations

import typing as t
from dataclasses import dataclass

from piccolo.columns.column_types import ForeignKey
from piccolo.columns.combination import And, Where
from piccolo.custom_types import Combinable, TableInstance
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    CallbackDelegate,
    CallbackType,
    LimitDelegate,
    OffsetDelegate,
    OrderByDelegate,
    OutputDelegate,
    PrefetchDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString
from piccolo.utils.dictionary import make_nested
from piccolo.utils.sync import run_sync

from .select import Select

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


@dataclass
class GetOrCreate:
    query: Objects
    where: Combinable
    defaults: t.Dict[t.Union[Column, str], t.Any]

    async def run(self):
        instance = await self.query.get(self.where).run()
        if instance:
            instance._was_created = False
            return instance

        instance = self.query.table()

        # If it's a complex `where`, there can be several column values to
        # extract e.g. (Band.name == 'Pythonistas') & (Band.popularity == 1000)
        if isinstance(self.where, Where):
            setattr(
                instance,
                self.where.column._meta.name,  # type: ignore
                self.where.value,  # type: ignore
            )
        elif isinstance(self.where, And):
            for column, value in self.where.get_column_values().items():
                if len(column._meta.call_chain) == 0:
                    # Make sure we only set the value if the column belongs
                    # to this table.
                    setattr(instance, column._meta.name, value)

        for column, value in self.defaults.items():
            if isinstance(column, str):
                column = instance._meta.get_column_by_name(column)
            setattr(instance, column._meta.name, value)

        await instance.save().run()

        instance._was_created = True

        return instance

    def __await__(self):
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self):
        return run_sync(self.run())

    def prefetch(self, *fk_columns) -> GetOrCreate:
        self.query.prefetch(*fk_columns)
        return self


@dataclass
class Create:
    query: Objects
    columns: t.Dict[str, t.Any]

    async def run(self):
        instance = self.query.table()

        for column, value in self.columns.items():
            if isinstance(column, str):
                column = instance._meta.get_column_by_name(column)
            setattr(instance, column._meta.name, value)

        await instance.save().run()

        instance._was_created = True

        return instance

    def __await__(self):
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self):
        return run_sync(self.run())


class Objects(Query, t.Generic[TableInstance]):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    __slots__ = (
        "nested",
        "limit_delegate",
        "offset_delegate",
        "order_by_delegate",
        "output_delegate",
        "callback_delegate",
        "prefetch_delegate",
        "where_delegate",
    )

    def __init__(
        self,
        table: t.Type[Table],
        prefetch: t.Sequence[t.Union[ForeignKey, t.List[ForeignKey]]] = (),
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.limit_delegate = LimitDelegate()
        self.offset_delegate = OffsetDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.output_delegate._output.as_objects = True
        self.callback_delegate = CallbackDelegate()
        self.prefetch_delegate = PrefetchDelegate()
        self.prefetch(*prefetch)
        self.where_delegate = WhereDelegate()

    def __new__(
        cls,
        table: t.Type[Table],
        prefetch: t.Sequence[t.Union[ForeignKey, t.List[ForeignKey]]] = (),
    ) -> ObjectsList[TableInstance]:
        """
        This is for MyPy, so we can tell it what values to expect when the
        query is run. By default it will be a list of objects. If the
        :meth:`first` or :meth:`get` methods are called, then a single object
        is returned instead.
        """
        instance = super().__new__(cls)
        return t.cast(ObjectsList[TableInstance], instance)

    def output(self: Self, load_json: bool = False) -> Self:
        self.output_delegate.output(
            as_list=False, as_json=False, load_json=load_json
        )
        return self

    def callback(
        self: Self,
        callbacks: t.Union[t.Callable, t.List[t.Callable]],
        *,
        on: CallbackType = CallbackType.success,
    ) -> Self:
        self.callback_delegate.callback(callbacks, on=on)
        return self

    def limit(self: Self, number: int) -> Self:
        self.limit_delegate.limit(number)
        return self

    def first(self: Self) -> ObjectsSingle[TableInstance]:
        self.limit_delegate.first()
        return t.cast(ObjectsSingle[TableInstance], self)

    def prefetch(
        self: Self, *fk_columns: t.Union[ForeignKey, t.List[ForeignKey]]
    ) -> Self:
        self.prefetch_delegate.prefetch(*fk_columns)
        return self

    def get(self: Self, where: Combinable) -> ObjectsSingle[TableInstance]:
        self.where_delegate.where(where)
        self.limit_delegate.first()
        return t.cast(ObjectsSingle[TableInstance], self)

    def offset(self: Self, number: int) -> Self:
        self.offset_delegate.offset(number)
        return self

    def get_or_create(
        self: Self,
        where: Combinable,
        defaults: t.Dict[t.Union[Column, str], t.Any] = None,
    ) -> GetOrCreate:
        if defaults is None:
            defaults = {}
        return GetOrCreate(query=self, where=where, defaults=defaults)

    def create(self: Self, **columns: t.Any) -> Create:
        return Create(query=self, columns=columns)

    def order_by(self: Self, *columns: Column, ascending=True) -> Self:
        self.order_by_delegate.order_by(*columns, ascending=ascending)
        return self

    def where(self: Self, *where: Combinable) -> Self:
        self.where_delegate.where(*where)
        return self

    async def batch(
        self: Self, batch_size: t.Optional[int] = None, **kwargs
    ) -> Batch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        return await self.table._meta.db.batch(self, **kwargs)

    async def response_handler(self, response):
        if self.limit_delegate._first:
            if len(response) == 0:
                return None
            if self.output_delegate._output.nested:
                return make_nested(response[0])
            else:
                return response[0]
        elif self.output_delegate._output.nested:
            return [make_nested(i) for i in response]
        else:
            return response

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        select = Select(table=self.table)

        for attr in (
            "limit_delegate",
            "where_delegate",
            "offset_delegate",
            "output_delegate",
            "order_by_delegate",
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


class ObjectsList(Objects, t.Generic[TableInstance]):
    """
    This is for MyPy.
    """

    async def run(
        self, node: t.Optional[str] = None, in_pool: bool = True
    ) -> t.List[TableInstance]:
        return await super().run(node=node, in_pool=in_pool)

    def __await__(
        self,
    ) -> t.Generator[None, None, t.List[TableInstance]]:
        return super().__await__()

    def run_sync(
        self, timed=False, in_pool=False, *args, **kwargs
    ) -> t.List[TableInstance]:
        return super().run_sync(timed, in_pool, *args, **kwargs)


class ObjectsSingle(Objects, t.Generic[TableInstance]):
    """
    This is for MyPy.
    """

    async def run(
        self, node: t.Optional[str] = None, in_pool: bool = True
    ) -> t.Optional[TableInstance]:
        return await super(Objects, self).run(node=node, in_pool=in_pool)

    def __await__(
        self,
    ) -> t.Generator[None, None, t.Optional[TableInstance]]:
        return super(Objects, self).__await__()

    def run_sync(
        self, timed=False, in_pool=False, *args, **kwargs
    ) -> t.Optional[TableInstance]:
        return super(Objects, self).run_sync(timed, in_pool, *args, **kwargs)


Self = t.TypeVar("Self", bound=t.Union[Objects, ObjectsSingle, ObjectsList])
