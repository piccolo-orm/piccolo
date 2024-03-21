from __future__ import annotations

import itertools
import json
import typing as t
from collections import defaultdict
from functools import partial

import pydantic

from piccolo.columns import Column
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Array,
    Decimal,
    Email,
    ForeignKey,
    Numeric,
    Text,
    Timestamptz,
    Varchar,
)
from piccolo.table import Table
from piccolo.utils.encoding import load_json

try:
    from pydantic.config import JsonDict
except ImportError:
    JsonDict = dict  # type: ignore


def pydantic_json_validator(value: t.Optional[str], required: bool = True):
    if value is None:
        if required:
            raise ValueError("The JSON value wasn't provided.")
        else:
            return value

    try:
        load_json(value)
    except json.JSONDecodeError as e:
        raise ValueError("Unable to parse the JSON.") from e
    else:
        return value


def is_table_column(column: Column, table: t.Type[Table]) -> bool:
    """
    Verify that the given ``Column`` belongs to the given ``Table``.
    """
    if column._meta.table is table:
        return True
    elif (
        column._meta.call_chain
        and column._meta.call_chain[0]._meta.table is table
    ):
        # We also allow the column if it's joined from the table.
        return True
    return False


def validate_columns(
    columns: t.Tuple[Column, ...], table: t.Type[Table]
) -> bool:
    """
    Verify that each column is a ``Column``` instance, and its parent is the
    given ``Table``.
    """
    return all(
        isinstance(column, Column)
        and is_table_column(column=column, table=table)
        for column in columns
    )


def get_array_value_type(
    column: Array, inner: t.Optional[t.Type] = None
) -> t.Type:
    """
    Gets the correct type for an ``Array`` column (which might be
    multidimensional).
    """
    if isinstance(column.base_column, Array):
        inner_type = get_array_value_type(column.base_column, inner=inner)
    else:
        inner_type = get_pydantic_value_type(column.base_column)

    return t.List[inner_type]  # type: ignore


def get_pydantic_value_type(column: Column) -> t.Type:
    """
    Map the Piccolo ``Column`` to a Pydantic type.
    """
    value_type: t.Type

    if isinstance(column, (Decimal, Numeric)):
        value_type = pydantic.condecimal(
            max_digits=column.precision, decimal_places=column.scale
        )
    elif isinstance(column, Email):
        value_type = pydantic.EmailStr  # type: ignore
    elif isinstance(column, Varchar):
        value_type = pydantic.constr(max_length=column.length)
    elif isinstance(column, Array):
        value_type = get_array_value_type(column=column)
    else:
        value_type = column.value_type

    return value_type


def create_pydantic_model(
    table: t.Type[Table],
    nested: t.Union[bool, t.Tuple[ForeignKey, ...]] = False,
    exclude_columns: t.Tuple[Column, ...] = (),
    include_columns: t.Tuple[Column, ...] = (),
    include_default_columns: bool = False,
    include_readable: bool = False,
    all_optional: bool = False,
    model_name: t.Optional[str] = None,
    deserialize_json: bool = False,
    recursion_depth: int = 0,
    max_recursion_depth: int = 5,
    pydantic_config: t.Optional[pydantic.config.ConfigDict] = None,
    json_schema_extra: t.Optional[t.Dict[str, t.Any]] = None,
) -> t.Type[pydantic.BaseModel]:
    """
    Create a Pydantic model representing a table.

    :param table:
        The Piccolo ``Table`` you want to create a Pydantic serialiser model
        for.
    :param nested:
        Whether ``ForeignKey`` columns are converted to nested Pydantic models.
        If ``False``, none are converted. If ``True``, they all are converted.
        If a tuple of ``ForeignKey`` columns is passed in, then only those are
        converted.
    :param exclude_columns:
        A tuple of ``Column`` instances that should be excluded from the
        Pydantic model. Only specify ``include_columns`` or
        ``exclude_columns``.
    :param include_columns:
        A tuple of ``Column`` instances that should be included in the
        Pydantic model. Only specify ``include_columns`` or
        ``exclude_columns``.
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
        By default, the values of any Piccolo ``JSON`` or ``JSONB`` columns are
        returned as strings. By setting this parameter to ``True``, they will
        be returned as objects.
    :param recursion_depth:
        Not to be set by the user - used internally to track recursion.
    :param max_recursion_depth:
        If using nested models, this specifies the max amount of recursion.
    :param pydantic_config:
        Allows you to configure some of Pydantic's behaviour. See the
        `Pydantic docs <https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict>`_
        for more info.
    :param json_schema_extra:
        This can be used to add additional fields to the schema. This is
        very useful when using Pydantic's JSON Schema features. For example:

        .. code-block:: python

            >>> my_model = create_pydantic_model(Band, my_extra_field="Hello")
            >>> my_model.model_json_schema()
            {..., "my_extra_field": "Hello"}

    :returns:
        A Pydantic model.

    """  # noqa: E501
    if exclude_columns and include_columns:
        raise ValueError(
            "`include_columns` and `exclude_columns` can't be used at the "
            "same time."
        )

    if recursion_depth == 0:
        if exclude_columns:
            if not validate_columns(columns=exclude_columns, table=table):
                raise ValueError(
                    f"`exclude_columns` are invalid: {exclude_columns!r}"
                )

        if include_columns:
            if not validate_columns(columns=include_columns, table=table):
                raise ValueError(
                    f"`include_columns` are invalid: {include_columns!r}"
                )

    ###########################################################################

    columns: t.Dict[str, t.Any] = {}
    validators: t.Dict[str, classmethod] = {}

    piccolo_columns = tuple(
        table._meta.columns
        if include_default_columns
        else table._meta.non_default_columns
    )

    if include_columns:
        include_columns_plus_ancestors = list(
            itertools.chain(
                include_columns, *[i._meta.call_chain for i in include_columns]
            )
        )
        piccolo_columns = tuple(
            i
            for i in piccolo_columns
            if any(
                i._equals(include_column)
                for include_column in include_columns_plus_ancestors
            )
        )

    if exclude_columns:
        piccolo_columns = tuple(
            i
            for i in piccolo_columns
            if not any(
                i._equals(exclude_column) for exclude_column in exclude_columns
            )
        )

    model_name = model_name or table.__name__

    for column in piccolo_columns:
        column_name = column._meta.name

        is_optional = True if all_optional else not column._meta.required

        #######################################################################
        # Work out the column type

        if isinstance(column, (JSON, JSONB)):
            if deserialize_json:
                value_type = pydantic.Json
            else:
                value_type = column.value_type
                validator = partial(
                    pydantic_json_validator, required=not is_optional
                )
                validators[
                    f"{column_name}_is_json"
                ] = pydantic.field_validator(column_name)(
                    validator  # type: ignore
                )
        else:
            value_type = get_pydantic_value_type(column=column)

        _type = t.Optional[value_type] if is_optional else value_type

        #######################################################################

        params: t.Dict[str, t.Any] = {}
        if is_optional:
            params["default"] = None

        if column._meta.db_column_name != column._meta.name:
            params["alias"] = column._meta.db_column_name

        extra: JsonDict = {
            "help_text": column._meta.help_text,
            "choices": column._meta.get_choices_dict(),
            "secret": column._meta.secret,
            "nullable": column._meta.null,
            "unique": column._meta.unique,
        }

        if isinstance(column, ForeignKey):
            if recursion_depth < max_recursion_depth and (
                (nested is True)
                or (
                    isinstance(nested, tuple)
                    and any(
                        column._equals(i)
                        for i in itertools.chain(
                            nested, *[i._meta.call_chain for i in nested]
                        )
                    )
                )
            ):
                nested_model_name = f"{model_name}.{column._meta.name}"
                _type = create_pydantic_model(
                    table=column._foreign_key_meta.resolved_references,
                    nested=nested,
                    include_columns=include_columns,
                    exclude_columns=exclude_columns,
                    include_default_columns=include_default_columns,
                    include_readable=include_readable,
                    all_optional=all_optional,
                    deserialize_json=deserialize_json,
                    recursion_depth=recursion_depth + 1,
                    max_recursion_depth=max_recursion_depth,
                    model_name=nested_model_name,
                )

            tablename = (
                column._foreign_key_meta.resolved_references._meta.tablename
            )
            target_column = (
                column._foreign_key_meta.resolved_target_column._meta.name
            )
            extra["foreign_key"] = {
                "to": tablename,
                "target_column": target_column,
            }

            if include_readable:
                columns[f"{column_name}_readable"] = (str, None)
        else:
            # This is used to tell Piccolo Admin that we want to display these
            # values using a specific widget.
            if isinstance(column, Text):
                extra["widget"] = "text-area"
            elif isinstance(column, (JSON, JSONB)):
                extra["widget"] = "json"
            elif isinstance(column, Timestamptz):
                extra["widget"] = "timestamptz"

            # It is useful for Piccolo API and Piccolo Admin to easily know
            # how many dimensions the array has.
            if isinstance(column, Array):
                extra["dimensions"] = column._get_dimensions()

        field = pydantic.Field(
            json_schema_extra={"extra": extra},
            **params,
        )

        columns[column_name] = (_type, field)

    pydantic_config = (
        pydantic_config.copy()
        if pydantic_config
        else pydantic.config.ConfigDict()
    )
    pydantic_config["arbitrary_types_allowed"] = True

    json_schema_extra_ = defaultdict(dict, **(json_schema_extra or {}))
    json_schema_extra_["extra"]["help_text"] = table._meta.help_text

    pydantic_config["json_schema_extra"] = dict(json_schema_extra_)

    model = pydantic.create_model(
        model_name,
        __config__=pydantic_config,
        __validators__=validators,
        **columns,
    )
    model.__qualname__ = model_name

    return model
