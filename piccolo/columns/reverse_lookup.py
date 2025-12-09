from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass

from piccolo.columns.base import QueryString, Selectable
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Column,
    LazyTableReference,
)
from piccolo.utils.sync import run_sync

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


class ReverseLookupSelect(Selectable):
    """
    This is a subquery used within a select to fetch reverse lookup data.
    """

    def __init__(
        self,
        *columns: Column,
        reverse_lookup: ReverseLookup,
        as_list: bool = False,
        load_json: bool = False,
        descending: bool = False,
    ):
        """
        :param columns:
            Which columns to include from the related table.
        :param as_list:
            If a single column is provided, and ``as_list`` is ``True`` a
            flattened list will be returned, rather than a list of objects.
        :param load_json:
            If ``True``, any JSON strings are loaded as Python objects.
        :param descending:
            If ``True'', reverse lookup results sorted in descending order,
            otherwise in default ascending order.

        """
        self.as_list = as_list
        self.columns = columns
        self.reverse_lookup = reverse_lookup
        self.load_json = load_json
        self.descending = descending

        safe_types = [int, str]

        # If the columns can be serialised / deserialise as JSON, then we
        # can fetch the data all in one go.
        self.serialisation_safe = all(
            (column.__class__.value_type in safe_types)
            and (type(column) not in (JSON, JSONB))
            for column in columns
        )

    def get_select_string(
        self, engine_type: str, with_alias=True
    ) -> QueryString:
        reverse_lookup_name = self.reverse_lookup._meta.name

        table1 = self.reverse_lookup._meta.table
        table1_pk = table1._meta.primary_key._meta.name
        table1_name = table1._meta.tablename

        table2 = self.reverse_lookup._meta.resolved_reverse_joining_table
        table2_name = table2._meta.tablename
        table2_pk = table2._meta.primary_key._meta.name
        table2_fk = self.reverse_lookup._meta.reverse_fk

        reverse_select = f"""
            "{table2_name}"
            WHERE "{table2_name}"."{table2_fk}"
                = "{table1_name}"."{table1_pk}"
        """

        if engine_type in ("postgres", "cockroach"):
            if self.as_list:
                column_name = self.columns[0]._meta.db_column_name
                return QueryString(
                    f"""
                    ARRAY(
                        SELECT
                            "{table2_name}"."{column_name}"
                        FROM {reverse_select}
                    ) AS "{reverse_lookup_name}"
                """
                )
            elif not self.serialisation_safe:
                column_name = table2_pk
                return QueryString(
                    f"""
                    ARRAY(
                        SELECT
                            "{table2_name}"."{column_name}"
                        FROM {reverse_select}
                    ) AS "{reverse_lookup_name}"
                """
                )
            else:
                if len(self.columns) > 0:
                    column_names = ", ".join(
                        f'"{table2_name}"."{column._meta.db_column_name}"'  # noqa: E501
                        for column in self.columns
                    )
                else:
                    column_names = ", ".join(
                        f'"{table2_name}"."{column._meta.db_column_name}"'  # noqa: E501
                        for column in table2._meta.columns
                    )
                return QueryString(
                    f"""
                    (
                        SELECT JSON_AGG("{table2_name}s")
                        FROM (
                            SELECT {column_names} FROM {reverse_select}
                        ) AS "{table2_name}s"
                    ) AS "{reverse_lookup_name}"
                """
                )
        elif engine_type == "sqlite":
            if len(self.columns) > 1 or not self.serialisation_safe:
                column_name = table2_pk
            else:
                try:
                    column_name = self.columns[0]._meta.db_column_name
                except IndexError:
                    column_name = table2_pk

            return QueryString(
                f"""
                (
                    SELECT group_concat(
                        "{table2_name}"."{column_name}"
                    )
                    FROM {reverse_select}
                )
                AS "{reverse_lookup_name} [M2M]"
            """
            )
        else:
            raise ValueError(f"{engine_type} is an unrecognised engine type")


@dataclass
class ReverseLookupMeta:
    reverse_joining_table: t.Union[t.Type[Table], LazyTableReference]
    reverse_fk: str

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None
    _table: t.Optional[t.Type[Table]] = None

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "`_name` isn't defined - the Table Metaclass should set it."
            )
        return self._name

    @property
    def table(self) -> t.Type[Table]:
        if not self._table:
            raise ValueError(
                "`_table` isn't defined - the Table Metaclass should set it."
            )
        return self._table

    @property
    def resolved_reverse_joining_table(self) -> t.Type[Table]:
        """
        Evaluates the ``reverse_joining_table`` attribute if it's a
        ``LazyTableReference``, raising a ``ValueError`` if it fails,
        otherwise returns a ``Table`` subclass.
        """
        from piccolo.table import Table

        if isinstance(self.reverse_joining_table, LazyTableReference):
            return self.reverse_joining_table.resolve()
        elif inspect.isclass(self.reverse_joining_table) and issubclass(
            self.reverse_joining_table, Table
        ):
            return self.reverse_joining_table
        else:
            raise ValueError(
                "The reverse_joining_table attribute is neither a Table"
                " subclass or a LazyTableReference instance."
            )


@dataclass
class ReverseLookupGetRelated:
    row: Table
    reverse_lookup: ReverseLookup

    async def run(self):
        primary_table = self.reverse_lookup._meta._table
        reverse_lookup_table = (
            self.reverse_lookup._meta.resolved_reverse_joining_table
        )

        for fk_column in reverse_lookup_table._meta.foreign_key_columns:
            ids = (
                await primary_table.select(
                    primary_table._meta.primary_key.join_on(
                        fk_column
                    ).all_columns()[0]
                )
                .where(primary_table._meta.primary_key == self.row)
                .output(as_list=True)
            )

        results = (
            await reverse_lookup_table.objects().where(
                reverse_lookup_table._meta.primary_key.is_in(ids)
            )
            if len(ids) > 0
            else []
        )

        return results

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


class ReverseLookup:
    def __init__(
        self,
        reverse_joining_table: t.Union[t.Type[Table], LazyTableReference],
        reverse_fk: str,
    ):
        """
        :param reverse_joining_table:
            A ``Table`` for reverse lookup.
        :param reverse_fk:
            The ForeignKey to be used for the reverse lookup.
        """
        self._meta = ReverseLookupMeta(
            reverse_joining_table=reverse_joining_table,
            reverse_fk=reverse_fk,
        )

    def __call__(
        self,
        *columns: Column,
        as_list: bool = False,
        load_json: bool = False,
        descending: bool = False,
    ) -> ReverseLookupSelect:
        """
        :param columns:
            Which columns to include from the related table. If none are
            specified, then all of the columns are returned.
        :param as_list:
            If a single column is provided, and ``as_list`` is ``True`` a
            flattened list will be returned, rather than a list of objects.
        :param load_json:
            If ``True``, any JSON strings are loaded as Python objects.
        :param descending:
            If ``True'', reverse lookup results sorted in descending order,
            otherwise in default ascending order.

        """

        if as_list and len(columns) != 1:
            raise ValueError(
                "`as_list` is only valid with a single column argument"
            )

        return ReverseLookupSelect(
            *columns,
            reverse_lookup=self,
            as_list=as_list,
            load_json=load_json,
            descending=descending,
        )
