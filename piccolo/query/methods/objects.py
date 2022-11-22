from __future__ import annotations

import typing as t
from dataclasses import dataclass

from piccolo.columns.column_types import ForeignKey
from piccolo.columns.combination import And, Where
from piccolo.custom_types import Combinable
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AsOfDelegate,
    CallbackDelegate,
    CallbackType,
    LimitDelegate,
    OffsetDelegate,
    OrderByDelegate,
    OrderByRaw,
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
    table_class: t.Type[Table]
    columns: t.Dict[str, t.Any]

    async def run(self):
        instance = self.table_class(**self.columns)
        await instance.save().run()
        return instance

    def __await__(self):
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self):
        return run_sync(self.run())


class Objects(Query):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    __slots__ = (
        "nested",
        "as_of_delegate",
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
        self.as_of_delegate = AsOfDelegate()
        self.limit_delegate = LimitDelegate()
        self.offset_delegate = OffsetDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.output_delegate._output.as_objects = True
        self.callback_delegate = CallbackDelegate()
        self.prefetch_delegate = PrefetchDelegate()
        self.prefetch(*prefetch)
        self.where_delegate = WhereDelegate()

    def output(self, load_json: bool = False) -> Objects:
        self.output_delegate.output(
            as_list=False, as_json=False, load_json=load_json
        )
        return self

    def callback(
        self,
        callbacks: t.Union[t.Callable, t.List[t.Callable]],
        *,
        on: CallbackType = CallbackType.success,
    ) -> Objects:
        self.callback_delegate.callback(callbacks, on=on)
        return self

    def as_of(self, interval: str = "-1s") -> Objects:
        self.as_of_delegate.as_of(interval)
        return self

    def limit(self, number: int) -> Objects:
        self.limit_delegate.limit(number)
        return self

    def first(self) -> Objects:
        self.limit_delegate.first()
        return self

    def prefetch(
        self, *fk_columns: t.Union[ForeignKey, t.List[ForeignKey]]
    ) -> Objects:
        self.prefetch_delegate.prefetch(*fk_columns)
        return self

    def get(self, where: Combinable) -> Objects:
        self.where_delegate.where(where)
        self.limit_delegate.first()
        return self

    def offset(self, number: int) -> Objects:
        self.offset_delegate.offset(number)
        return self

    def get_or_create(
        self,
        where: Combinable,
        defaults: t.Dict[t.Union[Column, str], t.Any] = None,
    ):
        if defaults is None:
            defaults = {}
        return GetOrCreate(query=self, where=where, defaults=defaults)

    def create(self, **columns: t.Any):
        return Create(table_class=self.table, columns=columns)

    def order_by(
        self,
        *columns: t.Union[Column, str, OrderByRaw],
        ascending: bool = True,
    ) -> Objects:
        _columns: t.List[t.Union[Column, OrderByRaw]] = []
        for column in columns:
            if isinstance(column, str):
                _columns.append(self.table._meta.get_column_by_name(column))
            else:
                _columns.append(column)

        self.order_by_delegate.order_by(*_columns, ascending=ascending)
        return self

    def where(self, *where: Combinable) -> Objects:
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
            "as_of_delegate",
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
