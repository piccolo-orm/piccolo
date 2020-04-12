from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.custom_types import Combinable
from piccolo.engine.base import Batch
from piccolo.query.base import Query
from piccolo.query.mixins import (
    LimitDelegate,
    OffsetDelegate,
    OrderByDelegate,
    WhereDelegate,
    OutputDelegate,
)
from piccolo.querystring import QueryString
from .select import Select

if t.TYPE_CHECKING:
    from piccolo.columns import Column
    from piccolo.table import Table


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

    def __init__(self, table: t.Type[Table]):
        super().__init__(table)
        self.limit_delegate = LimitDelegate()
        self.offset_delegate = OffsetDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.output_delegate = OutputDelegate()
        self.output_delegate._output.as_objects = True
        self.where_delegate = WhereDelegate()

    def limit(self, number: int) -> Objects:
        self.limit_delegate.limit(number)
        return self

    def first(self) -> Objects:
        self.limit_delegate.first()
        return self

    def offset(self, number: int) -> Objects:
        self.offset_delegate.offset(number)
        return self

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
    def querystrings(self) -> t.Sequence[QueryString]:
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
