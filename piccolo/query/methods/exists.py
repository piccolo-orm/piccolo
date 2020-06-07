from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.methods.select import Select
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from piccolo.table import Table


@dataclass
class Exists(Query):
    __slots__ = ("where_delegate",)

    def __init__(self, table: t.Type[Table]):
        super().__init__(table)
        self.where_delegate = WhereDelegate()

    def where(self, where: Combinable) -> Exists:
        self.where_delegate.where(where)
        return self

    async def response_handler(self, response) -> bool:
        # Convert to a bool - postgres returns True, and sqlite return 1.
        return bool(response[0]["exists"])

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        select = Select(table=self.table)
        select.where_delegate._where = self.where_delegate._where
        return [
            QueryString(
                'SELECT EXISTS({}) AS "exists"', select.querystrings[0]
            )
        ]
