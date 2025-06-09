from __future__ import annotations

import datetime
import inspect
import json
import typing as t
from decimal import Decimal
from functools import partial
from types import MappingProxyType

from piccolo.columns import JSON, JSONB, Array, Column, ForeignKey
from piccolo.custom_types import TableInstance
from piccolo.testing.random_builder import RandomBuilder
from piccolo.utils.sync import run_sync


class ModelBuilder:
    __DEFAULT_MAPPER: t.Dict[t.Type, t.Callable] = {}
    __OTHER_MAPPER: t.Dict[t.Type, t.Callable] = {}

    @classmethod
    async def build(
        cls,
        table_class: t.Type[TableInstance],
        defaults: t.Optional[t.Dict[t.Union[Column, str], t.Any]] = None,
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
        table_class: t.Type[TableInstance],
        defaults: t.Optional[t.Dict[t.Union[Column, str], t.Any]] = None,
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
        table_class: t.Type[TableInstance],
        defaults: t.Optional[t.Dict[t.Union[Column, str], t.Any]] = None,
        minimal: bool = False,
        persist: bool = True,
    ) -> TableInstance:
        model = table_class(_ignore_missing=True)
        defaults = defaults or {}

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
    def _randomize_attribute(cls, column: Column) -> t.Any:
        """
        Generate a random value for a column and apply formatting.

        :param column:
            Column class to randomize.

        """
        reg = cls.get_registry(column)
        if column._meta.choices:
            random_value = RandomBuilder.next_enum(column._meta.choices)
        else:
            random_value = reg[column.value_type]()

        if isinstance(column, (JSON, JSONB)):
            return json.dumps({"value": random_value})
        return random_value

    @classmethod
    def get_registry(
        cls, column: Column
    ) -> MappingProxyType[t.Type, t.Callable]:
        """
        This serves as the public API allowing users to **view**
        the complete registry for the specified column.

        :param column:
            Column class to randomize.

        """
        default_mapper = cls.__DEFAULT_MAPPER
        if not default_mapper:  # execute once only
            for typ, callable_ in RandomBuilder.get_mapper().items():
                default_mapper[typ] = callable_

        # order matters
        reg = {
            **default_mapper,
            **cls._get_local_mapper(column),
            **cls._get_other_mapper(column),
        }

        if column.value_type == list:
            reg[list] = partial(
                RandomBuilder.next_list,
                reg[t.cast(Array, column).base_column.value_type],
            )
        return MappingProxyType(reg)

    @classmethod
    def _get_local_mapper(cls, column: Column) -> t.Dict[t.Type, t.Callable]:
        """
        This classmethod encapsulates the desired logic, utilizing information
        from the column.

        :param column:
            Column class to randomize.
        """
        local_mapper: t.Dict[t.Type, t.Callable] = {}

        precision, scale = column._meta.params.get("digits") or (4, 2)
        local_mapper[Decimal] = partial(
            RandomBuilder.next_decimal, precision, scale
        )

        tz_aware = getattr(column, "tz_aware", False)
        local_mapper[datetime.datetime] = partial(
            RandomBuilder.next_datetime, tz_aware
        )

        if _length := column._meta.params.get("length"):
            local_mapper[str] = partial(RandomBuilder.next_str, _length)

        return local_mapper

    @classmethod
    def _get_other_mapper(cls, column: Column) -> t.Dict[t.Type, t.Callable]:
        """
        This is a hook that allows users to register their own random type
        callable. If the callable has a parameter named `column`, we assist
        by injecting `column` using `partial`.

        :param column:
            Column class to randomize.

        Examples::

            # a callable not utilizing column information
            ModelBuilder.register_random_type(str, lambda: "piccolo")

            # a callable utilizing the column information
            def next_str(column: Column) -> str:
                length = column._meta.params.get("length", 5)
                return "".join("a" for _ in range(length))
            )
            ModelBuilder.register_random_type(str, next_str)

        """
        other_mapper: t.Dict[t.Type, t.Callable] = {}
        for typ, callable_ in cls.__OTHER_MAPPER.items():
            sig = inspect.signature(callable_)
            if sig.parameters.get("column"):
                other_mapper[typ] = partial(callable_, column)
            else:
                other_mapper[typ] = callable_
        return other_mapper

    @classmethod
    def register_type(cls, typ: t.Type, callable_: t.Callable) -> None:
        cls.__OTHER_MAPPER[typ] = callable_

    @classmethod
    def unregister_type(cls, typ: t.Type) -> None:
        if typ in cls.__OTHER_MAPPER:
            del cls.__OTHER_MAPPER[typ]
