from __future__ import annotations

import datetime
import inspect
import json
import typing as t
from decimal import Decimal
from functools import partial

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
    def _randomize_attribute(cls, column: Column) -> t.Any:
        """
        Generate a random value for a column and apply formatting.

        :param column:
            Column class to randomize.

        """
        random_value: t.Any
        default_mapper = cls._get_default_mapper()
        local_mapper = cls._get_local_mapper(column)
        other_mapper = cls._get_other_mapper(column)
        # order matters
        mapper = {**default_mapper, **local_mapper, **other_mapper}

        if column._meta.choices:
            random_value = RandomBuilder.next_enum(column._meta.choices)
        elif column.value_type == list:
            length = RandomBuilder.next_int(maximum=10)
            base_type = t.cast(Array, column).base_column.value_type
            random_value = [mapper[base_type]() for _ in range(length)]
        else:
            random_value = mapper[column.value_type]()

        if isinstance(column, (JSON, JSONB)):
            return json.dumps({"value": random_value})
        return random_value

    @classmethod
    def _get_default_mapper(cls) -> t.Dict[t.Type, t.Callable]:
        """
        This classmethod encapsulates the desired logic.
        """
        mapper = cls.__DEFAULT_MAPPER
        if not mapper:  # execute once only
            for typ, callable_name in RandomBuilder.DEFAULT_MAPPER.items():
                # a simpler approach available?
                func = RandomBuilder.__dict__[callable_name].__func__
                mapper[typ] = partial(func, RandomBuilder)
        return mapper

    @classmethod
    def _get_local_mapper(cls, column: Column) -> t.Dict[t.Type, t.Callable]:
        """
        This classmethod encapsulates the desired logic, utilizing information
        from the column.

        :param column:
            Column class to randomize.
        """
        local_mapper: t.Dict[t.Type, t.Callable] = {}
        if column.value_type == Decimal:
            precision, scale = column._meta.params["digits"] or (4, 2)
            local_mapper[Decimal] = partial(
                RandomBuilder.next_decimal, precision, scale
            )
        elif column.value_type == datetime.datetime:
            tz_aware = getattr(column, "tz_aware", False)
            local_mapper[datetime.datetime] = partial(
                RandomBuilder.next_datetime, tz_aware
            )
        elif column.value_type == str:
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
    def register_random_type(cls, typ: t.Type, callable_: t.Callable) -> None:
        cls.__OTHER_MAPPER[typ] = callable_

    @classmethod
    def unregister_random_type(cls, typ: t.Type) -> None:
        if typ in cls.__OTHER_MAPPER:
            del cls.__OTHER_MAPPER[typ]
