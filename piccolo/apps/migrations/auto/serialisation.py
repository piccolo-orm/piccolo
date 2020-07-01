from __future__ import annotations
from copy import deepcopy
import datetime
from enum import Enum
from inspect import isclass
import typing as t
import uuid

from piccolo.columns import OnDelete, OnUpdate
from piccolo.custom_types import (
    DateDefault,
    TimeDefault,
    TimestampDefault,
    UUIDDefault,
)

from piccolo.table import Table


def serialise_params(params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    When writing column params to a migration file, we need to serialise some
    of the values.
    """
    params = deepcopy(params)

    # We currently don't support defaults which are functions.
    default = params.get("default", None)
    if hasattr(default, "__call__"):
        print(
            "Default arguments which are functions are not currently supported"
        )
        params["default"] = None

    for key, value in params.items():
        # Convert enums into plain values
        if isinstance(value, Enum):
            params[key] = str(value)

        # Replace any Table class values into class names
        if isclass(value) and issubclass(value, Table):
            params[key] = f"{value.__name__}|{value._meta.tablename}"

        # Convert any datetime, date, or time values into isoformat strings
        if isinstance(
            value, (datetime.datetime, datetime.date, datetime.time)
        ):
            params[key] = value.isoformat()

        # Convert any UUIDs into strings
        if isinstance(value, uuid.UUID):
            params[key] = str(value)

    return params


def deserialise_params(
    column_class_name: str, params: t.Dict[str, t.Any]
) -> t.Dict[str, t.Any]:
    """
    When reading column params from a migration file, we need to convert
    them from their serialised form.
    """
    params = deepcopy(params)

    references = params.get("references")
    if references:
        components = references.split("|")
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

        _Table: t.Type[Table] = type(
            references, (Table,), {},
        )
        if tablename:
            _Table._meta.tablename = tablename
        params["references"] = _Table

    on_delete = params.get("on_delete")
    if on_delete:
        enum_name, item_name = on_delete.split(".")
        if enum_name == "OnDelete":
            params["on_delete"] = getattr(OnDelete, item_name)

    on_update = params.get("on_update")
    if on_update:
        enum_name, item_name = on_update.split(".")
        if enum_name == "OnUpdate":
            params["on_update"] = getattr(OnUpdate, item_name)

    default = params.get("default")
    if isinstance(default, str):
        if column_class_name == "Timestamp":
            if default.startswith(("TimestampDefault", "DatetimeDefault")):
                _, item_name = default.split(".")
                params["default"] = getattr(TimestampDefault, item_name)
            else:
                try:
                    params["default"] = datetime.datetime.fromisoformat(
                        default
                    )
                except ValueError:
                    pass
        elif column_class_name == "Date":
            if default.startswith("DateDefault"):
                _, item_name = default.split(".")
                params["default"] = getattr(DateDefault, item_name)
            else:
                try:
                    params["default"] = datetime.date.fromisoformat(default)
                except ValueError:
                    pass
        elif column_class_name == "Time":
            if default.startswith("TimeDefault"):
                _, item_name = default.split(".")
                params["default"] = getattr(TimeDefault, item_name)
            else:
                try:
                    params["default"] = datetime.time.fromisoformat(default)
                except ValueError:
                    pass
        elif column_class_name == "UUID":
            if default.startswith("UUIDDefault"):
                _, item_name = default.split(".")
                params["default"] = getattr(UUIDDefault, item_name)
            else:
                try:
                    params["default"] = uuid.UUID(default)
                except ValueError:
                    pass

    return params
