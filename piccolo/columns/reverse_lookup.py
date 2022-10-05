from __future__ import annotations

import inspect
import typing as t
from dataclasses import dataclass

from piccolo.columns.base import Selectable
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Column,
    LazyTableReference,
)

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
        table: t.Type[Table],
    ):
        """
        :param columns:
            Which columns to include from the related table.
        :param as_list:
            If a single column is provided, and ``as_list`` is ``True`` a
            flattened list will be returned, rather than a list of objects.
        :param load_json:
            If ``True``, any JSON strings are loaded as Python objects.
        :param table:
            Parent table for reverse lookup.

        """
        self.as_list = as_list
        self.columns = columns
        self.reverse_lookup = reverse_lookup
        self.load_json = load_json
        self.table = table

        safe_types = [int, str]

        # If the columns can be serialised / deserialise as JSON, then we
        # can fetch the data all in one go.
        self.serialisation_safe = all(
            (column.__class__.value_type in safe_types)
            and (type(column) not in (JSON, JSONB))
            for column in columns
        )

    @property
    def foreign_key_columns_index(self) -> int:
        reverse_lookup_table = (
            self.reverse_lookup._meta.resolved_reverse_joining_table
        )
        fk_columns = [
            i._meta.name
            for i in reverse_lookup_table._meta.foreign_key_columns
        ]
        return fk_columns.index(self.table._meta.tablename)

    def get_select_string(self, engine_type: str, with_alias=True) -> str:
        reverse_lookup_table = (
            self.reverse_lookup._meta.resolved_reverse_joining_table
        )
        reverse_lookup_table_name = reverse_lookup_table._meta.tablename
        reverse_lookup_pk = reverse_lookup_table._meta.primary_key._meta.name
        reverse_lookup_fk_table_name = (
            reverse_lookup_table._meta.foreign_key_columns[
                self.foreign_key_columns_index
            ]._meta.name
        )
        reverse_lookup_fk = reverse_lookup_table._meta.foreign_key_columns[
            self.foreign_key_columns_index
        ]._meta.db_column_name

        reverse_select = f"""
            "{reverse_lookup_table_name}"
            JOIN "{reverse_lookup_fk_table_name}" "inner_{reverse_lookup_fk_table_name}" ON (
                "{reverse_lookup_table_name}"."{reverse_lookup_fk}"
                = "inner_{reverse_lookup_fk_table_name}"."{reverse_lookup_pk}"
            ) WHERE "{reverse_lookup_table_name}"."{reverse_lookup_fk}"
                = "{reverse_lookup_fk_table_name}"."{reverse_lookup_pk}"
        """  # noqa: E501

        if engine_type == "postgres":
            if self.as_list:
                column_name = self.columns[0]._meta.db_column_name
                return f"""
                    ARRAY(
                        SELECT
                            "{reverse_lookup_table_name}"."{column_name}"
                        FROM {reverse_select}
                    ) AS "{reverse_lookup_table_name}s"
                """
            elif not self.serialisation_safe:
                column_name = reverse_lookup_pk
                return f"""
                    ARRAY(
                        SELECT
                            "{reverse_lookup_table_name}"."{column_name}"
                        FROM {reverse_select}
                    ) AS "{reverse_lookup_table_name}s"
                """
            else:
                if len(self.columns) > 0:
                    column_names = ", ".join(
                        f'"{reverse_lookup_table_name}"."{column._meta.db_column_name}"'  # noqa: E501
                        for column in self.columns
                    )
                else:
                    column_names = ", ".join(
                        f'"{reverse_lookup_table_name}"."{column._meta.db_column_name}"'  # noqa: E501
                        for column in reverse_lookup_table._meta.columns
                    )
                return f"""
                    (
                        SELECT JSON_AGG("{reverse_lookup_table_name}s")
                        FROM (
                            SELECT {column_names} FROM {reverse_select}
                        ) AS "{reverse_lookup_table_name}s"
                    ) AS "{reverse_lookup_table_name}s"
                """
        elif engine_type == "sqlite":
            if len(self.columns) > 1 or not self.serialisation_safe:
                column_name = reverse_lookup_pk
            else:
                try:
                    column_name = self.columns[0]._meta.db_column_name
                except IndexError:
                    column_name = reverse_lookup_pk

            return f"""
                (
                    SELECT group_concat(
                        "{reverse_lookup_table_name}"."{column_name}"
                    )
                    FROM {reverse_select}
                )
                AS "{reverse_lookup_table_name}s [M2M]"
            """
        else:
            raise ValueError(f"{engine_type} is an unrecognised engine type")


@dataclass
class ReverseLookupMeta:
    reverse_joining_table: t.Union[t.Type[Table], LazyTableReference]

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


class ReverseLookup:
    def __init__(
        self,
        reverse_joining_table: t.Union[t.Type[Table], LazyTableReference],
    ):
        """
        :param reverse_joining_table:
            A ``Table`` for reverse lookup.
        """
        self._meta = ReverseLookupMeta(
            reverse_joining_table=reverse_joining_table,
        )

    def __call__(
        self,
        *columns: Column,
        as_list: bool = False,
        load_json: bool = False,
        table: t.Type[Table],
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
        :param table:
            Parent table for reverse lookup.

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
            table=table,
        )
