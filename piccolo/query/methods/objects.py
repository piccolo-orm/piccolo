from __future__ import annotations
import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import (
    LimitDelegate, OrderByDelegate, WhereDelegate, OutputDelegate, Output
)
from piccolo.querystring import QueryString
from .select import Select

if t.TYPE_CHECKING:
    from piccolo.columns import Column


class Objects(Query):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    def setup_delegates(self):
        self.limit_delegate = LimitDelegate()
        self.order_by_delegate = OrderByDelegate()
        self.where_delegate = WhereDelegate()
        self.output_delegate = OutputDelegate()
        self.output_delegate._output.as_objects = True

    def limit(self, number: int) -> Objects:
        self.limit_delegate.limit(number)
        return self

    def first(self) -> Objects:
        self.limit_delegate.first()
        return self

    def order_by(self, *columns: Column, ascending=True) -> Objects:
        self.order_by_delegate.order_by(*columns, ascending=ascending)
        return self

    def where(self, where: Combinable) -> Objects:
        self.where_delegate.where(where)
        return self

    def response_handler(self, response):
        if self.limit_delegate._first:
            if len(response) == 0:
                raise ValueError('No results found')
            else:
                return response[0]
        else:
            return response

    @property
    def querystring(self) -> QueryString:
        select = Select(
            table=self.table,
            column_names=[]
        )

        for attr in ('limit_delegate', 'where_delegate', 'output_delegate',
                     'order_by_delegate'):
            setattr(select, attr, getattr(self, attr))

        return select.querystring

    def __str__(self) -> str:
        return self.querystring.__str__()
