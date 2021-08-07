import json
import typing as t
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID

from piccolo.columns.base import Column
from piccolo.table import Table
from piccolo.testing.exceptions import InvalidColumnError
from piccolo.testing.random_builder import RandomBuilder


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

    def __init__(self, minimal: bool = False, persist: bool = True):
        """
        Configurations for ModelBuilder

        :param minimal:
            If set, only required and non-nullable fields will be randomized.

        :param persist:
            If set, random model will not persisted by default.

        """
        self.minimal = minimal
        self.persist = persist

    def build(self, table_class: t.Type[Table], **attrs) -> Table:
        """
        Build Table instance with random data. It can build relationships,
        all supported data types and parameters.

        :param table_class:
            Table class to randomize.

        Examples:

            manager = ModelBuilder.build(Manager)
            manager = ModelBuilder.build(Manager, name='Guido')
            manager = ModelBuilder(persist=False).build(Manager)
            manager = ModelBuilder(minimal=True).build(Manager)
            band = ModelBuilder.build(Band, manager=manager)
        """
        model = table_class()
        column_names = [column._meta.name for column in model._meta.columns]

        for name, value in attrs.items():
            if name not in column_names:
                raise InvalidColumnError(
                    f"Table {model.__class__.__name__} has no column {name}"
                )

            setattr(model, name, value)

        for column in model._meta.columns:

            if column._meta.null and self.minimal:
                continue

            if column._meta.name in attrs:
                continue  # Column value exists

            if "references" in column._meta.params and self.persist:
                reference_model = self.build(column._meta.params["references"])
                reference_model.save().run_sync()
                random_value = getattr(
                    reference_model,
                    reference_model._meta.primary_key._meta.name,
                )
            else:
                random_value = self.__randomize_attribute(column)

            setattr(model, column._meta.name, random_value)

        if self.persist:
            model.save().run_sync()

        return model

    @classmethod
    def __randomize_attribute(cls, column: Column) -> t.Any:
        """
        Generate a random value for a column and apply formattings.

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
