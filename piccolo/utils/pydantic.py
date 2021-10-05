from __future__ import annotations

import json
import typing as t
import uuid
from functools import lru_cache

import pydantic

from piccolo.columns import Column
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Array,
    Decimal,
    ForeignKey,
    Numeric,
    Secret,
    Text,
    Varchar,
)
from piccolo.table import Table
from piccolo.utils.encoding import load_json

try:
    from asyncpg.pgproto.pgproto import UUID  # type: ignore
except ImportError:
    JSON_ENCODERS = {uuid.UUID: lambda i: str(i)}
else:
    JSON_ENCODERS = {uuid.UUID: lambda i: str(i), UUID: lambda i: str(i)}


class Config(pydantic.BaseConfig):
    json_encoders = JSON_ENCODERS
    arbitrary_types_allowed = True


def pydantic_json_validator(cls, value):
    try:
        load_json(value)
    except json.JSONDecodeError:
        raise ValueError("Unable to parse the JSON.")
    else:
        return value


@lru_cache()
def create_pydantic_model(
    table: t.Type[Table],
    nested: bool = False,
    exclude_columns: t.Tuple[Column, ...] = (),
    include_default_columns: bool = False,
    include_readable: bool = False,
    all_optional: bool = False,
    model_name: t.Optional[str] = None,
    deserialize_json: bool = False,
) -> t.Type[pydantic.BaseModel]:
    """
    Create a Pydantic model representing a table.

    :param table:
        The Piccolo ``Table`` you want to create a Pydantic serialiser model
        for.
    :param nested:
        Whether ``ForeignKey`` columns are converted to nested Pydantic models.
    :param exclude_columns:
        A tuple of ``Column`` instances that should be excluded from the
        Pydantic model.
    :param include_default_columns:
        Whether to include columns like ``id`` in the serialiser. You will
        typically include these columns in GET requests, but don't require
        them in POST requests.
    :param include_readable:
        Whether to include 'readable' columns, which give a string
        representation of a foreign key.
    :param all_optional:
        If True, all fields are optional. Useful for filters etc.
    :param model_name:
        By default, the classname of the Piccolo ``Table`` will be used, but
        you can override it if you want multiple Pydantic models based off the
        same Piccolo table.
    :param deserialize_json:
        By default, the values of any Piccolo JSON or JSONB columns are
        returned as strings. By setting this parameter to True, they will be
        returned as objects.
    :returns:
        A Pydantic model.

    """
    columns: t.Dict[str, t.Any] = {}
    validators: t.Dict[str, classmethod] = {}
    piccolo_columns = (
        table._meta.columns
        if include_default_columns
        else table._meta.non_default_columns
    )

    if not all(
        isinstance(column, Column)
        # Make sure that every column is tied to the current Table
        and column._meta.table is table
        for column in exclude_columns
    ):
        raise ValueError(f"Exclude columns ({exclude_columns!r}) are invalid.")

    for column in piccolo_columns:
        # normal __contains__ checks __eq__ as well which returns ``Where``
        # instance which always evaluates to ``True``
        if any(column is obj for obj in exclude_columns):
            continue

        column_name = column._meta.name

        is_optional = True if all_optional else not column._meta.required

        #######################################################################

        # Work out the column type

        if isinstance(column, (Decimal, Numeric)):
            value_type: t.Type = pydantic.condecimal(
                max_digits=column.precision, decimal_places=column.scale
            )
        elif isinstance(column, Varchar):
            value_type = pydantic.constr(max_length=column.length)
        elif isinstance(column, Array):
            value_type = t.List[column.base_column.value_type]  # type: ignore
        elif isinstance(column, (JSON, JSONB)):
            if deserialize_json:
                value_type = pydantic.Json
            else:
                value_type = column.value_type
                validators[f"{column_name}_is_json"] = pydantic.validator(
                    column_name, allow_reuse=True
                )(pydantic_json_validator)
        else:
            value_type = column.value_type

        _type = t.Optional[value_type] if is_optional else value_type

        #######################################################################

        params: t.Dict[str, t.Any] = {
            "default": None if is_optional else ...,
            "nullable": column._meta.null,
        }

        if column._meta.db_column_name != column._meta.name:
            params["alias"] = column._meta.db_column_name

        extra = {
            "help_text": column._meta.help_text,
            "choices": column._meta.get_choices_dict(),
        }

        if isinstance(column, ForeignKey):
            if nested:
                _type = create_pydantic_model(
                    table=column._foreign_key_meta.resolved_references,
                    nested=True,
                    include_default_columns=include_default_columns,
                    include_readable=include_readable,
                    all_optional=all_optional,
                    deserialize_json=deserialize_json,
                )

            tablename = (
                column._foreign_key_meta.resolved_references._meta.tablename
            )
            field = pydantic.Field(
                extra={"foreign_key": True, "to": tablename, **extra},
                **params,
            )
            if include_readable:
                columns[f"{column_name}_readable"] = (str, None)
        elif isinstance(column, Text):
            field = pydantic.Field(format="text-area", extra=extra, **params)
        elif isinstance(column, (JSON, JSONB)):
            field = pydantic.Field(format="json", extra=extra, **params)
        elif isinstance(column, Secret):
            field = pydantic.Field(extra={"secret": True, **extra})
        else:
            field = pydantic.Field(extra=extra, **params)

        columns[column_name] = (_type, field)

    model_name = model_name or table.__name__

    class CustomConfig(Config):
        schema_extra = {"help_text": table._meta.help_text}

    return pydantic.create_model(
        model_name,
        __config__=CustomConfig,
        __validators__=validators,
        **columns,
    )
