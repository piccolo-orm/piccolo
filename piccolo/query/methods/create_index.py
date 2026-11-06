from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Union

from piccolo.columns import Column
from piccolo.columns.indexes import IndexMethod
from piccolo.query.base import DDL

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


IndexParamValue = Union[bool, int, float, str]

# An unquoted Postgres identifier.
IDENTIFIER_REGEX = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")

# An operator class, which can be schema qualified - for example
# ``gin_trgm_ops`` or ``extensions.gin_trgm_ops``.
OPERATOR_CLASS_REGEX = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_$]*(\.[A-Za-z_][A-Za-z0-9_$]*)?$"
)


def validate_operator_class(operator_class: str) -> str:
    if not isinstance(operator_class, str) or not OPERATOR_CLASS_REGEX.match(
        operator_class
    ):
        raise ValueError(
            f"{operator_class!r} isn't a valid operator class - for example "
            "'gin_trgm_ops' or 'extensions.gin_trgm_ops'."
        )
    return operator_class


def format_index_param_value(value: IndexParamValue) -> str:
    # bool is a subclass of int, so check it first.
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str) and IDENTIFIER_REGEX.match(value):
        return value
    raise ValueError(
        f"{value!r} isn't a valid index parameter value - it must be a bool, "
        "int, float, or a keyword like 'auto'."
    )


def format_index_params(index_params: Mapping[str, IndexParamValue]) -> str:
    params = []
    for key, value in index_params.items():
        if not isinstance(key, str) or not IDENTIFIER_REGEX.match(key):
            raise ValueError(f"{key!r} isn't a valid index parameter name.")
        params.append(f"{key}={format_index_param_value(value)}")
    return ", ".join(params)


class CreateIndex(DDL):
    def __init__(
        self,
        table: type[Table],
        columns: Union[list[Column], list[str]],
        method: IndexMethod = IndexMethod.btree,
        if_not_exists: bool = False,
        operator_class: Optional[str] = None,
        index_params: Optional[Mapping[str, IndexParamValue]] = None,
        **kwargs,
    ):
        """
        :param operator_class:
            Postgres only. The operator class to use for each column - for
            example ``'gin_trgm_ops'`` or ``'vector_cosine_ops'``.
        :param index_params:
            Postgres only. Storage parameters for the index, added as a
            ``WITH (...)`` clause - for example ``{'m': 16}``. Values must be
            a ``bool``, ``int``, ``float``, or a keyword like ``'auto'``.

        """
        if operator_class is not None:
            validate_operator_class(operator_class)
        if index_params:
            format_index_params(index_params)

        self.columns = columns
        self.method = method
        self.if_not_exists = if_not_exists
        self.operator_class = operator_class
        self.index_params = index_params
        super().__init__(table, **kwargs)

    async def run(self, in_pool: bool = True):
        engine = self.table._meta.db
        if engine and engine.engine_type == "postgres":
            from piccolo.engine.extensions import check_extensions_for_index

            await check_extensions_for_index(
                engine, self.method, self.operator_class, in_pool=in_pool
            )
        return await super().run(in_pool=in_pool)

    @property
    def column_names(self) -> list[str]:
        return [
            i._meta.db_column_name if isinstance(i, Column) else i
            for i in self.columns
        ]

    @property
    def prefix(self) -> str:
        prefix = "CREATE INDEX"
        if self.if_not_exists:
            prefix += " IF NOT EXISTS"
        return prefix

    @property
    def postgres_ddl(self) -> Sequence[str]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.get_formatted_tablename()
        method_name = self.method.value
        if self.operator_class:
            operator_class = validate_operator_class(self.operator_class)
            column_names_str = ", ".join(
                [f'"{i}" {operator_class}' for i in self.column_names]
            )
        else:
            column_names_str = ", ".join([f'"{i}"' for i in self.column_names])
        ddl = (
            f"{self.prefix} {index_name} ON {tablename} USING "
            f"{method_name} ({column_names_str})"
        )
        if self.index_params:
            ddl += f" WITH ({format_index_params(self.index_params)})"
        return [ddl]

    @property
    def cockroach_ddl(self) -> Sequence[str]:
        return self.postgres_ddl

    @property
    def sqlite_ddl(self) -> Sequence[str]:
        column_names = self.column_names
        index_name = self.table._get_index_name(column_names)
        tablename = self.table._meta.get_formatted_tablename()

        method_name = self.method.value
        if method_name != "btree":
            raise ValueError("SQLite only support btree indexes.")

        if self.operator_class or self.index_params:
            raise ValueError(
                "SQLite doesn't support `operator_class` or `index_params`."
            )

        column_names_str = ", ".join([f'"{i}"' for i in self.column_names])
        return [
            (
                f"{self.prefix} {index_name} ON {tablename} "
                f"({column_names_str})"
            )
        ]
