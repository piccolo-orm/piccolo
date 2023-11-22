from __future__ import annotations

import typing as t

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.mixins import (
    ReturningDelegate,
    ValuesDelegate,
    WhereDelegate,
)
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column


class UpdateError(Exception):
    pass


class Update(Query[TableInstance, t.List[t.Any]]):
    __slots__ = (
        "force",
        "returning_delegate",
        "values_delegate",
        "where_delegate",
    )

    def __init__(
        self, table: t.Type[TableInstance], force: bool = False, **kwargs
    ):
        super().__init__(table, **kwargs)
        self.force = force
        self.returning_delegate = ReturningDelegate()
        self.values_delegate = ValuesDelegate(table=table)
        self.where_delegate = WhereDelegate()

    ###########################################################################
    # Clauses

    def values(
        self,
        values: t.Optional[t.Dict[t.Union[Column, str], t.Any]] = None,
        **kwargs,
    ) -> Update:
        if values is None:
            values = {}
        values = dict(values, **kwargs)
        self.values_delegate.values(values)
        return self

    def where(self, *where: Combinable) -> Update:
        self.where_delegate.where(*where)
        return self

    def returning(self, *columns: Column) -> Update:
        self.returning_delegate.returning(columns)
        return self

    ###########################################################################

    def _validate(self):
        """
        Called at the start of :meth:`piccolo.query.base.Query.run` to make
        sure the user has configured the query correctly before running it.
        """
        if len(self.values_delegate._values) == 0:
            raise ValueError("No values were specified to update.")

        for column, _ in self.values_delegate._values.items():
            if len(column._meta.call_chain) > 0:
                raise ValueError(
                    "Related values can't be updated via an update."
                )

        if (not self.where_delegate._where) and (not self.force):
            classname = self.table.__name__
            raise UpdateError(
                "Do you really want to update all rows in "
                f"{classname}? If so, use pass `force=True` into "
                f"`{classname}.update`. Otherwise, add a where clause."
            )

    ###########################################################################

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        columns_str = ", ".join(
            f'"{col._meta.db_column_name}" = {{}}'
            for col, _ in self.values_delegate._values.items()
        )

        query = f"UPDATE {self.table._meta.get_formatted_tablename()} SET {columns_str}"  # noqa: E501

        querystring = QueryString(
            query, *self.values_delegate.get_sql_values()
        )

        if self.where_delegate._where:
            # The JOIN syntax isn't allowed in SQL UPDATE queries, so we need
            # to write the WHERE clause differently, using a sub select.

            querystring = QueryString(
                "{} WHERE {}",
                querystring,
                self.where_delegate._where.querystring_for_update,
            )

        if self.returning_delegate._returning:
            querystring = QueryString(
                "{}{}",
                querystring,
                self.returning_delegate._returning.querystring,
            )

        return [querystring]
