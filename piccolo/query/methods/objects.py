from __future__ import annotations

import typing as t

from piccolo.columns.column_types import ForeignKey
from piccolo.columns.combination import And, Where
from piccolo.custom_types import Combinable, TableInstance
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
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
from piccolo.query.proxy import Proxy
from piccolo.querystring import QueryString
from piccolo.utils.dictionary import make_nested
from piccolo.utils.sync import run_sync

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column


###############################################################################


class GetOrCreate(
    Proxy["Objects[TableInstance]", TableInstance], t.Generic[TableInstance]
):
    def __init__(
        self,
        query: Objects[TableInstance],
        table_class: t.Type[TableInstance],
        where: Combinable,
        defaults: t.Dict[Column, t.Any],
    ):
        self.query = query
        self.table_class = table_class
        self.where = where
        self.defaults = defaults

    async def run(
        self, node: t.Optional[str] = None, in_pool: bool = True
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

        instance = self.table_class(_data=self.defaults)

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

        instance = t.cast(TableInstance, instance)
        instance._was_created = True
        return instance


class Get(
    Proxy["First[TableInstance]", t.Optional[TableInstance]],
    t.Generic[TableInstance],
):
    pass


class First(
    Proxy["Objects[TableInstance]", t.Optional[TableInstance]],
    t.Generic[TableInstance],
):
    async def run(
        self, node: t.Optional[str] = None, in_pool: bool = True
    ) -> t.Optional[TableInstance]:
        objects = await self.query.run(
            node=node, in_pool=in_pool, use_callbacks=False
        )

        results = objects[0] if objects else None

        modified_response: t.Optional[TableInstance] = (
            await self.query.callback_delegate.invoke(
                results=results, kind=CallbackType.success
            )
        )
        return modified_response


class Create(t.Generic[TableInstance]):
    """
    This is provided as a simple convenience. Rather than running::

        band = Band(name='Pythonistas')
        await band.save()

    We can instead do it in a single line::

        band = Band.objects().create(name='Pythonistas')

    """

    def __init__(
        self,
        table_class: t.Type[TableInstance],
        columns: t.Dict[str, t.Any],
    ):
        self.table_class = table_class
        self.columns = columns

    async def run(
        self,
        node: t.Optional[str] = None,
        in_pool: bool = True,
    ) -> TableInstance:
        instance = self.table_class(**self.columns)
        await instance.save().run(node=node, in_pool=in_pool)
        return instance

    def __await__(self) -> t.Generator[None, None, TableInstance]:
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self, *args, **kwargs) -> TableInstance:
        return run_sync(self.run(*args, **kwargs))


###############################################################################


class Objects(
    Query[TableInstance, t.List[TableInstance]], t.Generic[TableInstance]
):
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
        table: t.Type[TableInstance],
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

    def as_of(self, interval: str = "-1s") -> Objects:
        if self.engine_type != "cockroach":
            raise NotImplementedError("Only CockroachDB supports AS OF")
        self.as_of_delegate.as_of(interval)
        return self

    def limit(self: Self, number: int) -> Self:
        self.limit_delegate.limit(number)
        return self

    def prefetch(
        self: Self, *fk_columns: t.Union[ForeignKey, t.List[ForeignKey]]
    ) -> Self:
        self.prefetch_delegate.prefetch(*fk_columns)
        return self

    def offset(self: Self, number: int) -> Self:
        self.offset_delegate.offset(number)
        return self

    def order_by(
        self: Self, *columns: t.Union[Column, str, OrderByRaw], ascending=True
    ) -> Self:
        _columns: t.List[t.Union[Column, OrderByRaw]] = []
        for column in columns:
            if isinstance(column, str):
                _columns.append(self.table._meta.get_column_by_name(column))
            else:
                _columns.append(column)

        self.order_by_delegate.order_by(*_columns, ascending=ascending)
        return self

    def where(self: Self, *where: Combinable) -> Self:
        self.where_delegate.where(*where)
        return self

    ###########################################################################

    def first(self: Self) -> First[TableInstance]:
        self.limit_delegate.limit(1)
        return First[TableInstance](query=self)

    def get(self: Self, where: Combinable) -> Get[TableInstance]:
        self.where_delegate.where(where)
        self.limit_delegate.limit(1)
        return Get[TableInstance](query=First[TableInstance](query=self))

    def get_or_create(
        self: Self,
        where: Combinable,
        defaults: t.Optional[t.Dict[Column, t.Any]] = None,
    ) -> GetOrCreate[TableInstance]:
        if defaults is None:
            defaults = {}
        return GetOrCreate[TableInstance](
            query=self, table_class=self.table, where=where, defaults=defaults
        )

    def create(self: Self, **columns: t.Any) -> Create[TableInstance]:
        return Create[TableInstance](table_class=self.table, columns=columns)

    ###########################################################################

    async def batch(
        self: Self,
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
        if self.output_delegate._output.nested:
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

    ###########################################################################

    async def run(
        self,
        node: t.Optional[str] = None,
        in_pool: bool = True,
        use_callbacks: bool = True,
    ) -> t.List[TableInstance]:
        results = await super().run(node=node, in_pool=in_pool)

        if use_callbacks:
            # With callbacks, the user can return any data that they want.
            # Assume that most of the time they will still return a list of
            # Table instances.
            modified: t.List[TableInstance] = (
                await self.callback_delegate.invoke(
                    results, kind=CallbackType.success
                )
            )
            return modified
        else:
            return results

    def __await__(
        self,
    ) -> t.Generator[None, None, t.List[TableInstance]]:
        return super().__await__()


Self = t.TypeVar("Self", bound=Objects)
