from __future__ import annotations

import typing as t
from enum import Enum

from piccolo.utils.encoding import dump_json

if t.TYPE_CHECKING:
    from piccolo.columns import Column


def convert_to_sql_value(value: t.Any, column: Column) -> t.Any:
    """
    Some values which can be passed into Piccolo queries aren't valid in the
    database. For example, Enums, Table instances, and dictionaries for JSON
    columns.
    """
    from piccolo.columns.column_types import JSON, JSONB
    from piccolo.table import Table

    if isinstance(value, Table):
        return getattr(value, value._meta.primary_key._meta.name)
    elif isinstance(value, Enum):
        return value.value
    elif isinstance(column, (JSON, JSONB)) and not isinstance(value, str):
        return dump_json(value)
    else:
        return value
