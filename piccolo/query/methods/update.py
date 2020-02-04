from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import ValuesDelegate, WhereDelegate
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:
    from piccolo.columns import Column
    from piccolo.table import Table


@dataclass
class Update(Query):

    __slots__ = ("values_delegate", "where_delegate")

    def __init__(self, table: t.Type[Table]):
        super().__init__(table)
        self.values_delegate = ValuesDelegate()
        self.where_delegate = WhereDelegate()

    def values(self, values: t.Dict[Column, t.Any]) -> Update:
        self.values_delegate.values(values)
        return self

    def where(self, where: Combinable) -> Update:
        self.where_delegate.where(where)
        return self

    def validate(self):
        if len(self.values_delegate._values) == 0:
            raise ValueError(
                "No values were specified to update - please use .values"
            )

        for column, value in self.values_delegate._values.items():
            if len(column._meta.call_chain) > 0:
                raise ValueError(
                    "Related values can't be updated via an update"
                )

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        self.validate()

        columns_str = ", ".join(
            [
                f"{col._meta.name} = {{}}"
                for col, _ in self.values_delegate._values.items()
            ]
        )

        query = f"UPDATE {self.table._meta.tablename} SET " + columns_str

        querystring = QueryString(
            query, *self.values_delegate._values.values()
        )

        if self.where_delegate._where:
            where_querystring = QueryString(
                "{} WHERE {}",
                querystring,
                self.where_delegate._where.querystring,
            )
            return [where_querystring]
        else:
            return [querystring]
