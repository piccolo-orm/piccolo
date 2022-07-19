import json
import typing as t
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from piccolo.columns import Array, Column
from piccolo.table import Table
from piccolo.testing.random_builder import RandomBuilder
from piccolo.utils.sync import run_sync


class ModelBuilder:
    __DEFAULT_MAPPER: t.Dict[t.Type, t.Callable] = {
        bool: RandomBuilder.next_bool,
        bytes: RandomBuilder.next_bytes,
        date: RandomBuilder.next_date,
        datetime: RandomBuilder.next_datetime,
        float: RandomBuilder.next_float,
        int: RandomBuilder.next_int,
        str: RandomBuilder.next_str,
        time: RandomBuilder.next_time,
        timedelta: RandomBuilder.next_timedelta,
        UUID: RandomBuilder.next_uuid,
    }

    @classmethod
    async def build(
        cls,
        table_class: t.Type[Table],
        defaults: t.Dict[t.Union[Column, str], t.Any] = None,
        persist: bool = True,
        minimal: bool = False,
    ) -> Table:
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
        table_class: t.Type[Table],
        defaults: t.Dict[t.Union[Column, str], t.Any] = None,
        persist: bool = True,
        minimal: bool = False,
    ) -> Table:
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
        table_class: t.Type[Table],
        defaults: t.Dict[t.Union[Column, str], t.Any] = None,
        minimal: bool = False,
        persist: bool = True,
    ) -> Table:
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

            if "references" in column._meta.params and persist:
                reference_model = await cls._build(
                    column._meta.params["references"],
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
    def _randomize_attribute(cls, column: Column) -> t.Any:
        """
        Generate a random value for a column and apply formatting.

        :param column:
            Column class to randomize.

        """
        random_value: t.Any
        if column.value_type == Decimal:
            precision, scale = column._meta.params["digits"]
            random_value = RandomBuilder.next_float(
                maximum=10 ** (precision - scale), scale=scale
            )
        elif column.value_type == list:
            length = RandomBuilder.next_int(maximum=10)
            base_type = t.cast(Array, column).base_column.value_type
            random_value = [
                cls.__DEFAULT_MAPPER[base_type]() for _ in range(length)
            ]
        elif column._meta.choices:
            random_value = RandomBuilder.next_enum(column._meta.choices)
        else:
            random_value = cls.__DEFAULT_MAPPER[column.value_type]()

        if "length" in column._meta.params and isinstance(random_value, str):
            return random_value[: column._meta.params["length"]]
        elif column.column_type in ["JSON", "JSONB"]:
            return json.dumps(random_value)

        return random_value
