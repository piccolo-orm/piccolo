from __future__ import annotations

from piccolo.query.base import Query
from piccolo.query.mixins import LimitMixin, OrderByMixin, WhereMixin, Output
from piccolo.querystring import QueryString
from .select import Select


class Objects(
    Query,
    LimitMixin,
    OrderByMixin,
    WhereMixin,
):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    _output = Output(as_objects=True)

    @property
    def querystring(self) -> QueryString:
        select = Select(
            table=self.table,
            column_names=[]
        )

        for attr in ('_limit', '_where', '_output', 'order_by'):
            setattr(select, attr, getattr(self, attr))

        return select.querystring

    def __str__(self) -> str:
        return self.querystring.__str__()
