from __future__ import annotations

import datetime
from typing import Any

from piccolo.columns.column_types import OnDelete, OnUpdate
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.table import create_table_class


def deserialise_legacy_params(name: str, value: str) -> Any:
    """
    Earlier versions of Piccolo serialised parameters differently. This is
    here purely for backwards compatibility.
    """
    if name == "references":
        components = value.split("|")
        if len(components) == 1:
            class_name = components[0]
            tablename = None
        elif len(components) == 2:
            class_name, tablename = components
        else:
            raise ValueError(
                "Unrecognised Table serialisation - should either be "
                "`SomeClassName` or `SomeClassName|some_table_name`."
            )

        return create_table_class(
            class_name=class_name,
            class_kwargs={"tablename": tablename} if tablename else {},
        )

    ###########################################################################

    if name == "default":
        if value in {"TimestampDefault.now", "DatetimeDefault.now"}:
            return TimestampNow()
        try:
            _value = datetime.datetime.fromisoformat(value)
        except ValueError:
            pass
        else:
            return _value

    elif name == "on_delete":
        enum_name, item_name = value.split(".")
        if enum_name == "OnDelete":
            return getattr(OnDelete, item_name)

    elif name == "on_update":
        enum_name, item_name = value.split(".")
        if enum_name == "OnUpdate":
            return getattr(OnUpdate, item_name)

    return value
