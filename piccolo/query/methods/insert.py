from __future__ import annotations

import typing as t

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AddDelegate,
    OnConflictAction,
    OnConflictDelegate,
    ReturningDelegate,
)
from piccolo.querystring import QueryString

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Column
    from piccolo.table import Table


class Insert(
    t.Generic[TableInstance], Query[TableInstance, t.List[t.Dict[str, t.Any]]]
):
    __slots__ = ("add_delegate", "on_conflict_delegate", "returning_delegate")

    def __init__(
        self, table: t.Type[TableInstance], *instances: TableInstance, **kwargs
    ):
        super().__init__(table, **kwargs)
        self.add_delegate = AddDelegate()
        self.returning_delegate = ReturningDelegate()
        self.on_conflict_delegate = OnConflictDelegate()
        self.add(*instances)

    ###########################################################################
    # Clauses

    def add(self: Self, *instances: Table) -> Self:
        self.add_delegate.add(*instances, table_class=self.table)
        return self

    def returning(self: Self, *columns: Column) -> Self:
        self.returning_delegate.returning(columns)
        return self

    def on_conflict(
        self: Self,
        target: t.Optional[t.Union[str, Column, t.Tuple[Column, ...]]] = None,
        action: t.Union[
            OnConflictAction, t.Literal["DO NOTHING", "DO UPDATE"]
        ] = OnConflictAction.do_nothing,
        values: t.Optional[
            t.Sequence[t.Union[Column, t.Tuple[Column, t.Any]]]
        ] = None,
        where: t.Optional[Combinable] = None,
    ) -> Self:
        if (
            self.engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() < 3.24
        ):
            raise NotImplementedError(
                "SQLite versions lower than 3.24 don't support ON CONFLICT"
            )

        if (
            self.engine_type in ("postgres", "cockroach")
            and len(self.on_conflict_delegate._on_conflict.on_conflict_items)
            == 1
        ):
            raise NotImplementedError(
                "Postgres and Cockroach only support a single ON CONFLICT "
                "clause."
            )

        self.on_conflict_delegate.on_conflict(
            target=target,
            action=action,
            values=values,
            where=where,
        )
        return self

    ###########################################################################

    def _raw_response_callback(self, results: t.List):
        """
        Assign the ids of the created rows to the model instances.
        """
        for index, row in enumerate(results):
            table_instance: Table = self.add_delegate._add[index]
            setattr(
                table_instance,
                self.table._meta.primary_key._meta.name,
                row.get(
                    self.table._meta.primary_key._meta.db_column_name, None
                ),
            )
            table_instance._exists_in_db = True

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        base = f"INSERT INTO {self.table._meta.get_formatted_tablename()}"
        columns = ",".join(
            f'"{i._meta.db_column_name}"' for i in self.table._meta.columns
        )
        values = ",".join("{}" for _ in self.add_delegate._add)
        query = f"{base} ({columns}) VALUES {values}"
        querystring = QueryString(
            query,
            *[i.querystring for i in self.add_delegate._add],
            query_type="insert",
            table=self.table,
        )

        engine_type = self.engine_type

        on_conflict = self.on_conflict_delegate._on_conflict
        if on_conflict.on_conflict_items:
            querystring = QueryString(
                "{}{}",
                querystring,
                on_conflict.querystring,
                query_type="insert",
                table=self.table,
            )

        if engine_type in ("postgres", "cockroach") or (
            engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() >= 3.35
        ):
            returning = self.returning_delegate._returning
            if returning:
                return [
                    QueryString(
                        "{}{}",
                        querystring,
                        returning.querystring,
                        query_type="insert",
                        table=self.table,
                    )
                ]

        return [querystring]


Self = t.TypeVar("Self", bound=Insert)
