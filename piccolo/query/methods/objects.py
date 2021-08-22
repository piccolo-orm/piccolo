from __future__ import annotations

import typing as t
from dataclasses import dataclass

from piccolo.custom_types import Combinable
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    LimitDelegate,
    OffsetDelegate,
    OrderByDelegate,
    OutputDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString
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
        instance = await self.query.where(self.where).first().run()
        if instance:
            return instance

        instance = self.query.table()
        setattr(
            instance,
            self.where.column._meta.name,  # type: ignore
            self.where.value,  # type: ignore
        )

        for column, value in self.defaults.items():
            if isinstance(column, str):
                column = instance._meta.get_column_by_name(column)
            setattr(instance, column._meta.name, value)

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


@dataclass
class Objects(Query):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    __slots__ = (
        "limit_delegate",
        "offset_delegate",
        "order_by_delegate",
        "output_delegate",
        "where_delegate",
    )

    def __init__(self, table: t.Type[Table], **kwargs):
        super().__init__(table, **kwargs)
        self.limit_delegate = LimitDelegate()
        self.offset_delegate = OffsetDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.output_delegate._output.as_objects = True
        self.where_delegate = WhereDelegate()

    def output(self, load_json: bool = False) -> Objects:
        self.output_delegate.output(
            as_list=False, as_json=False, load_json=load_json
        )
        return self

    def limit(self, number: int) -> Objects:
        self.limit_delegate.limit(number)
        return self

    def first(self) -> Objects:
        self.limit_delegate.first()
        return self

    def offset(self, number: int) -> Objects:
        self.offset_delegate.offset(number)
        return self

    def get_or_create(
        self,
        where: Combinable,
        defaults: t.Dict[t.Union[Column, str], t.Any] = {},
    ):
        return GetOrCreate(query=self, where=where, defaults=defaults)

    def order_by(self, *columns: Column, ascending=True) -> Objects:
        self.order_by_delegate.order_by(*columns, ascending=ascending)
        return self

    def where(self, where: Combinable) -> Objects:
        self.where_delegate.where(where)
        return self

    async def batch(
        self, batch_size: t.Optional[int] = None, **kwargs
    ) -> Batch:
        if batch_size:
            kwargs.update(batch_size=batch_size)
        return await self.table._meta.db.batch(self, **kwargs)

    async def response_handler(self, response):
        if self.limit_delegate._first:
            if len(response) == 0:
                return None
            else:
                return response[0]
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

        return select.querystrings
