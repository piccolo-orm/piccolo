from __future__ import annotations
from dataclasses import dataclass
import typing as t

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import WhereDelegate
from piccolo.querystring import QueryString


class DeletionError(Exception):
    pass


@dataclass
class Delete(Query):

    __slots__ = tuple()

    force: bool = False

    def __post_init__(self):
        self.where_delegate = WhereDelegate()

    def where(self, where: Combinable) -> Delete:
        self.where_delegate.where(where)
        return self

    def _validate(self):
        """
        Don't let a deletion happen unless it has a where clause, or is
        explicitly forced.
        """
        if (not self.where_delegate._where) and (not self.force):
            classname = self.table.__name__
            raise DeletionError(
                "Do you really want to delete all the data from "
                f"{classname}? If so, use {classname}.delete(force=True)."
            )

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        query = f"DELETE FROM {self.table._meta.tablename}"
        if self.where_delegate._where:
            query += " WHERE {}"
            return [QueryString(query, self.where_delegate._where.querystring)]
        else:
            return [QueryString(query)]
