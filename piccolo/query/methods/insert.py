from __future__ import annotations

import typing as t

from piccolo.custom_types import TableInstance
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AddDelegate,
    OnConflict,
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
    __slots__ = (
        "add_delegate",
        "returning_delegate",
        "on_conflict_delegate",
    )

    def __init__(
        self,
        table: t.Type[TableInstance],
        on_conflict: t.Optional[OnConflict] = None,
        *instances: TableInstance,
        **kwargs,
    ):
        super().__init__(table, **kwargs)
        self.add_delegate = AddDelegate()
        self.returning_delegate = ReturningDelegate()
        self.on_conflict_delegate = OnConflictDelegate()
        self.on_conflict(on_conflict)  # type: ignore
        self.add(*instances)

    ###########################################################################
    # Clauses

    def add(self: Self, *instances: Table) -> Self:
        self.add_delegate.add(*instances, table_class=self.table)
        return self

    def returning(self: Self, *columns: Column) -> Self:
        self.returning_delegate.returning(columns)
        return self

    def on_conflict(self: Self, conflict: OnConflict) -> Self:
        self.on_conflict_delegate.on_conflict(conflict)
        return self

    ###########################################################################

    def _raw_response_callback(self, results):
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
        engine_type = self.engine_type
        if (
            engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() < 3.24
        ):  # pragma: no cover
            if self.on_conflict_delegate._on_conflict == OnConflict.do_nothing:
                base = f'INSERT OR IGNORE INTO "{self.table._meta.tablename}"'
            else:
                base = f'INSERT OR REPLACE INTO "{self.table._meta.tablename}"'
        else:
            base = f'INSERT INTO "{self.table._meta.tablename}"'
        columns = ",".join(
            f'"{i._meta.db_column_name}"' for i in self.table._meta.columns
        )
        values = ",".join("{}" for _ in self.add_delegate._add)
        if self.on_conflict_delegate._on_conflict is not None:
            if self.on_conflict_delegate._on_conflict == OnConflict.do_nothing:
                query = f"""
                {base} ({columns}) VALUES {values} ON CONFLICT
                {self.on_conflict_delegate._on_conflict.value}
                """
            else:
                excluded_updated_columns = ", ".join(
                    f"{i._meta.db_column_name}=EXCLUDED.{i._meta.db_column_name}"  # noqa: E501
                    for i in self.table._meta.columns
                )
                query = f"""
                {base} ({columns}) VALUES {values} ON CONFLICT
                ({self.table._meta.primary_key._meta.name})
                {self.on_conflict_delegate._on_conflict.value}
                SET {excluded_updated_columns}
                """
        else:
            query = f"{base} ({columns}) VALUES {values}"
        querystring = QueryString(
            query,
            *[i.querystring for i in self.add_delegate._add],
            query_type="insert",
            table=self.table,
        )

        if engine_type in ("postgres", "cockroach") or (
            engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() >= 3.35
        ):
            if self.returning_delegate._returning:
                return [
                    QueryString(
                        "{}{}",
                        querystring,
                        self.returning_delegate._returning.querystring,
                        query_type="insert",
                        table=self.table,
                    )
                ]

        return [querystring]


Self = t.TypeVar("Self", bound=Insert)
