import json
import typing as t
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from piccolo.columns.base import Column
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
        Build Table instance with random data and save async.
        This can build relationships, supported data types and parameters.

        :param table_class:
            Table class to randomize.

        Examples:
            manager = await ModelBuilder.build(Manager)
            manager = await ModelBuilder.build(Manager, name='Guido')
            manager = await ModelBuilder(persist=False).build(Manager)
            manager = await ModelBuilder(minimal=True).build(Manager)
            band = await ModelBuilder.build(Band, manager=manager)

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
        Build Table instance with random data and save sync.
        This can build relationships, supported data types and parameters.

        :param table_class:
            Table class to randomize.

        Examples:
            manager = ModelBuilder.build_sync(Manager)
            manager = ModelBuilder.build_sync(Manager, name='Guido')
            manager = ModelBuilder(persist=False).build_sync(Manager)
            manager = ModelBuilder(minimal=True).build_sync(Manager)
            band = ModelBuilder.build_sync(Band, manager=manager)

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
        model = table_class()
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
        if column.value_type == Decimal:
            precision, scale = column._meta.params["digits"]
            random_value = RandomBuilder.next_float(
                maximum=10 ** (precision - scale), scale=scale
            )
        elif column._meta.choices:
            random_value = RandomBuilder.next_enum(column._meta.choices)
        else:
            random_value = cls.__DEFAULT_MAPPER[column.value_type]()

        if "length" in column._meta.params and isinstance(random_value, str):
            return random_value[: column._meta.params["length"]]
        elif column.column_type in ["JSON", "JSONB"]:
            return json.dumps(random_value)

        return random_value
