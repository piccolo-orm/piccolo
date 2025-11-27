from __future__ import annotations

from collections.abc import Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    Literal,
    Optional,
    TypeVar,
    Union,
)

from piccolo.custom_types import Combinable, TableInstance
from piccolo.query.base import Query
from piccolo.query.mixins import (
    AddDelegate,
    OnConflictAction,
    OnConflictDelegate,
    ReturningDelegate,
)
from piccolo.querystring import QueryString

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Column
    from piccolo.table import Table


class Insert(
    Generic[TableInstance], Query[TableInstance, list[dict[str, Any]]]
):
    __slots__ = ("add_delegate", "on_conflict_delegate", "returning_delegate")

    def __init__(
        self, table: type[TableInstance], *instances: TableInstance, **kwargs
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
        target: Optional[Union[str, Column, tuple[Column, ...]]] = None,
        action: Union[
            OnConflictAction, Literal["DO NOTHING", "DO UPDATE"]
        ] = OnConflictAction.do_nothing,
        values: Optional[Sequence[Union[Column, tuple[Column, Any]]]] = None,
        where: Optional[Combinable] = None,
    ) -> Self:
        if (
            self.engine_type == "sqlite"
            and self.table._meta.db.get_version_sync() < 3.24
        ):
            raise NotImplementedError(
                "SQLite versions lower than 3.24 don't support ON CONFLICT"
            )

        if (
            self.engine_type in ("postgres", "cockroach", "mysql")
            and len(self.on_conflict_delegate._on_conflict.on_conflict_items)
            == 1
        ):
            raise NotImplementedError(
                "Postgres, Cockroach and MySQL only support a single "
                "ON CONFLICT clause."
            )

        self.on_conflict_delegate.on_conflict(
            target=target,
            action=action,
            values=values,
            where=where,
        )
        return self

    ###########################################################################

    def _raw_response_callback(self, results: list):
        """
        Assign the ids of the created rows to the model instances.
        """
        try:
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
        except IndexError:
            ...

    @property
    def mysql_insert_ignore(self) -> bool:
        # detect DO_NOTHING action for MySQL
        for item in self.on_conflict_delegate._on_conflict.on_conflict_items:
            if item.action == OnConflictAction.do_nothing:
                return True
        return False

    @property
    def default_querystrings(self) -> Sequence[QueryString]:
        if self.engine_type == "mysql" and self.mysql_insert_ignore:
            base = f"INSERT IGNORE INTO {self.table._meta.get_formatted_tablename()}"  # noqa: E501
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
            return [querystring]

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


Self = TypeVar("Self", bound=Insert)
