from __future__ import annotations

import functools
import typing as t
from enum import Enum

from piccolo.utils.encoding import dump_json
from piccolo.utils.warnings import colored_warning

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column


def convert_to_sql_value(value: t.Any, column: Column) -> t.Any:
    """
    Some values which can be passed into Piccolo queries aren't valid in the
    database. For example, Enums, Table instances, and dictionaries for JSON
    columns.
    """
    from piccolo.columns.column_types import JSON, JSONB, ForeignKey
    from piccolo.table import Table

    if isinstance(value, Table):
        if isinstance(column, ForeignKey):
            return getattr(
                value,
                column._foreign_key_meta.resolved_target_column._meta.name,
            )
        elif column._meta.primary_key:
            return getattr(value, column._meta.name)
        else:
            raise ValueError(
                "Table instance provided, and the column isn't a ForeignKey, "
                "or primary key column."
            )
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(column, (JSON, JSONB)) and not isinstance(value, str):
        return None if value is None else dump_json(value)
    elif isinstance(value, list):
        if len(value) > 100:
            colored_warning(
                "When using large lists, consider bypassing the ORM and "
                "using SQL directly for improved performance."
            )
        # Attempt to do this as performantly as possible.
        func = functools.partial(convert_to_sql_value, column=column)
        return list(map(func, value))
    else:
        return value
