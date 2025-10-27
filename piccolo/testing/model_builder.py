from __future__ import annotations

import datetime
import decimal
import json
from collections.abc import Callable
from decimal import Decimal
from typing import Any, Optional, Union, cast
from uuid import UUID

from piccolo.columns import JSON, JSONB, Array, Column, ForeignKey
from piccolo.custom_types import TableInstance
from piccolo.testing.random_builder import RandomBuilder
from piccolo.utils.sync import run_sync


class ModelBuilder:
    __DEFAULT_MAPPER: dict[type, Callable] = {
        bool: RandomBuilder.next_bool,
        bytes: RandomBuilder.next_bytes,
        datetime.date: RandomBuilder.next_date,
        datetime.datetime: RandomBuilder.next_datetime,
        float: RandomBuilder.next_float,
        decimal.Decimal: RandomBuilder.next_decimal,
        int: RandomBuilder.next_int,
        str: RandomBuilder.next_str,
        datetime.time: RandomBuilder.next_time,
        datetime.timedelta: RandomBuilder.next_timedelta,
        UUID: RandomBuilder.next_uuid,
    }

    @classmethod
    async def build(
        cls,
        table_class: type[TableInstance],
        defaults: Optional[dict[Union[Column, str], Any]] = None,
        persist: bool = True,
        minimal: bool = False,
    ) -> TableInstance:
        """
        Build a ``Table`` instance with random data and save async.
        If the ``Table`` has any foreign keys, then the related rows are also
        created automatically.

        :param table_class:
            Table class to randomize.
        :param defaults:
            Any values specified here will be used instead of random values.
        :param persist:
            Whether to save the new instance in the database.
        :param minimal:
            If ``True`` then any columns with ``null=True`` are assigned
            a value of ``None``.

        Examples::

            # Create a new instance with all random values:
            manager = await ModelBuilder.build(Manager)

            # Create a new instance, with certain defaults:
            manager = await ModelBuilder.build(
                Manager,
                {Manager.name: 'Guido'}
            )

            # Create a new instance, but don't save it in the database:
            manager = await ModelBuilder.build(Manager, persist=False)

            # Create a new instance, with all null values set to None:
            manager = await ModelBuilder.build(Manager, minimal=True)

            # We can pass other table instances in as default values:
            band = await ModelBuilder.build(Band, {Band.manager: manager})

        """
        return await cls._build(
            table_class=table_class,
            defaults=defaults,
            persist=persist,
            minimal=minimal,
        )

    @classmethod
    def build_sync(
        cls,
        table_class: type[TableInstance],
        defaults: Optional[dict[Union[Column, str], Any]] = None,
        persist: bool = True,
        minimal: bool = False,
    ) -> TableInstance:
        """
        A sync wrapper around :meth:`build`.
        """
        return run_sync(
            cls.build(
                table_class=table_class,
                defaults=defaults,
                persist=persist,
                minimal=minimal,
            )
        )

    @classmethod
    async def _build(
        cls,
        table_class: type[TableInstance],
        defaults: Optional[dict[Union[Column, str], Any]] = None,
        minimal: bool = False,
        persist: bool = True,
    ) -> TableInstance:
        model = table_class(_ignore_missing=True)
        defaults = {} if not defaults else defaults

        for column, value in defaults.items():
            if isinstance(column, str):
                column = model._meta.get_column_by_name(column)

            setattr(model, column._meta.name, value)

        for column in model._meta.columns:
            if column._meta.null and minimal:
                continue

            if column._meta.name in defaults:
                continue  # Column value exists

            if isinstance(column, ForeignKey) and persist:
                # Check for recursion
                if column._foreign_key_meta.references is table_class:
                    if column._meta.null is True:
                        # We can avoid this problem entirely by setting it to
                        # None.
                        random_value = None
                    else:
                        # There's no way to avoid recursion in the situation.
                        raise ValueError("Recursive foreign key detected")
                else:
                    reference_model = await cls._build(
                        column._foreign_key_meta.resolved_references,
                        persist=True,
                    )
                    random_value = getattr(
                        reference_model,
                        reference_model._meta.primary_key._meta.name,
                    )
            else:
                random_value = cls._randomize_attribute(column)

            setattr(model, column._meta.name, random_value)

        if persist:
            await model.save().run()

        return model

    @classmethod
    def _randomize_attribute(cls, column: Column) -> Any:
        """
        Generate a random value for a column and apply formatting.

        :param column:
            Column class to randomize.

        """
        random_value: Any
        if column.value_type == Decimal:
            precision, scale = column._meta.params["digits"] or (4, 2)
            random_value = RandomBuilder.next_decimal(
                precision=precision, scale=scale
            )
        elif column.value_type == datetime.datetime:
            tz_aware = getattr(column, "tz_aware", False)
            random_value = RandomBuilder.next_datetime(tz_aware=tz_aware)
        elif column.value_type == list:
            length = RandomBuilder.next_int(maximum=10)
            base_type = cast(Array, column).base_column.value_type
            random_value = [
                cls.__DEFAULT_MAPPER[base_type]() for _ in range(length)
            ]
        elif column._meta.choices:
            random_value = RandomBuilder.next_enum(column._meta.choices)
        else:
            random_value = cls.__DEFAULT_MAPPER[column.value_type]()

        if "length" in column._meta.params and isinstance(random_value, str):
            return random_value[: column._meta.params["length"]]
        elif isinstance(column, (JSON, JSONB)):
            return json.dumps({"value": random_value})

        return random_value
