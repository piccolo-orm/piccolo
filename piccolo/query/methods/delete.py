from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeVar, Union

from piccolo.custom_types import Combinable
from piccolo.query.base import Query
from piccolo.query.mixins import ReturningDelegate, WhereDelegate
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


class DeletionError(Exception):
    pass


class Delete(Query):

    __slots__ = (
        "force",
        "returning_delegate",
        "where_delegate",
    )

    def __init__(self, table: type[Table], force: bool = False, **kwargs):
        super().__init__(table, **kwargs)
        self.force = force
        self.returning_delegate = ReturningDelegate()
        self.where_delegate = WhereDelegate()

    def where(self: Self, *where: Union[Combinable, QueryString]) -> Self:
        self.where_delegate.where(*where)
        return self

    def returning(self: Self, *columns: Column) -> Self:
        self.returning_delegate.returning(columns)
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
                f"{classname}? If so, use {classname}.delete(force=True). "
                "Otherwise, add a where clause."
            )

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        query = f"DELETE FROM {self.table._meta.get_formatted_tablename()}"

        querystring = QueryString(query)

        if self.where_delegate._where:
            querystring = QueryString(
                "{} WHERE {}",
                querystring,
                self.where_delegate._where.querystring_for_update_and_delete,
            )

        if self.returning_delegate._returning:
            querystring = QueryString(
                "{}{}",
                querystring,
                self.returning_delegate._returning.querystring,
            )

        return [querystring]


Self = TypeVar("Self", bound=Delete)
