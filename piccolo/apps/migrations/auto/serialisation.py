from __future__ import annotations

import builtins
import datetime
import decimal
import inspect
import typing as t
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum

from piccolo.columns import Column
from piccolo.columns.defaults.base import Default
from piccolo.columns.reference import LazyTableReference
from piccolo.table import Table
from piccolo.utils.repr import repr_class_instance

from .serialisation_legacy import deserialise_legacy_params

###############################################################################


@dataclass
class SerialisedBuiltin:
    builtin: t.Any

    def __hash__(self):
        return hash(self.builtin.__name__)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return self.builtin.__name__


@dataclass
class SerialisedClassInstance:
    instance: object

    def __hash__(self):
        return self.instance.__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return repr_class_instance(self.instance)


@dataclass
class SerialisedColumnInstance:
    instance: Column
    serialised_params: SerialisedParams

    def __hash__(self):
        return self.instance.__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        args = ", ".join(
            [
                f"{key}={self.serialised_params.params.get(key).__repr__()}"  # noqa: E501
                for key in self.instance._meta.params.keys()
            ]
        )
        return f"{self.instance.__class__.__name__}({args})"


@dataclass
class SerialisedEnumInstance:
    instance: Enum

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return f"{self.instance.__class__.__name__}.{self.instance.name}"


@dataclass
class SerialisedTableType:
    table_type: t.Type[Table]

    def __hash__(self):
        return hash(
            f"{self.table_type._meta.tablename}-{self.table_type.__name__}"
        )

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        tablename = self.table_type._meta.tablename
        class_name = self.table_type.__name__

        # We have to add the primary key column definition too, so foreign
        # keys can be created with the correct type.
        pk_column = self.table_type._meta.primary_key
        pk_column_name = pk_column._meta.name
        serialised_pk_column = SerialisedColumnInstance(
            pk_column,
            serialised_params=serialise_params(params=pk_column._meta.params),
        )

        return (
            f'class {class_name}(Table, tablename="{tablename}"): '
            f"{pk_column_name} = {serialised_pk_column}"
        )

    def __lt__(self, other):
        return repr(self) < repr(other)


@dataclass
class SerialisedEnumType:
    enum_type: t.Type[Enum]

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        class_name = self.enum_type.__name__
        params = {i.name: i.value for i in self.enum_type}
        return f"Enum('{class_name}', {params})"


@dataclass
class SerialisedCallable:
    callable_: t.Callable

    def __hash__(self):
        return hash(self.callable_.__name__)

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return self.callable_.__name__


@dataclass
class SerialisedUUID:
    instance: uuid.UUID

    def __hash__(self):
        return self.instance.int

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return f"UUID('{str(self.instance)}')"


###############################################################################


@dataclass
class Import:
    module: str
    target: str

    def __repr__(self):
        return f"from {self.module} import {self.target}"

    def __hash__(self):
        return hash(f"{self.module}-{self.target}")

    def __lt__(self, other):
        return repr(self) < repr(other)


@dataclass
class SerialisedParams:
    params: t.Dict[str, t.Any]
    extra_imports: t.List[Import]
    extra_definitions: t.List[str] = field(default_factory=list)


###############################################################################


def serialise_params(params: t.Dict[str, t.Any]) -> SerialisedParams:
    """
    When writing column params to a migration file, we need to serialise some
    of the values.
    """
    params = deepcopy(params)
    extra_imports: t.List[Import] = []
    extra_definitions: t.List[t.Any] = []

    for key, value in params.items():

        # Builtins, such as str, list and dict.
        if inspect.getmodule(value) == builtins:
            params[key] = SerialisedBuiltin(builtin=value)
            continue

        # Column instances, which are used by Array definitions.
        if isinstance(value, Column):
            column: Column = value
            serialised_params: SerialisedParams = serialise_params(
                params=column._meta.params
            )

            # Include the extra imports and definitions required for the
            # column params.
            extra_imports.extend(serialised_params.extra_imports)
            extra_definitions.extend(serialised_params.extra_definitions)

            extra_imports.append(
                Import(
                    module=column.__class__.__module__,
                    target=column.__class__.__name__,
                )
            )
            params[key] = SerialisedColumnInstance(
                instance=value, serialised_params=serialised_params
            )
            continue

        # Class instances
        if isinstance(value, Default):
            params[key] = SerialisedClassInstance(instance=value)
            extra_imports.append(
                Import(
                    module=value.__class__.__module__,
                    target=value.__class__.__name__,
                )
            )
            continue

        # Dates and times
        if isinstance(
            value, (datetime.time, datetime.datetime, datetime.date)
        ):
            # Already has a good __repr__.
            extra_imports.append(
                Import(
                    module=value.__class__.__module__,
                    target=value.__class__.__name__,
                )
            )
            continue

        # UUIDs
        if isinstance(value, uuid.UUID):
            params[key] = SerialisedUUID(instance=value)
            extra_imports.append(Import(module="uuid", target="UUID"))
            continue

        # Decimals
        if isinstance(value, decimal.Decimal):
            # Already has a good __repr__.
            extra_imports.append(Import(module="decimal", target="Decimal"))
            continue

        # Enum instances
        if isinstance(value, Enum):
            if value.__module__.startswith("piccolo"):
                # It's an Enum defined within Piccolo, so we can safely import
                # it.
                params[key] = SerialisedEnumInstance(instance=value)
                extra_imports.append(
                    Import(
                        module=value.__module__,
                        target=value.__class__.__name__,
                    )
                )
            else:
                # It's a user defined Enum, so we'll insert the raw value.
                enum_serialised_params: SerialisedParams = serialise_params(
                    params={key: value.value}
                )
                params[key] = enum_serialised_params.params[key]
                extra_imports.extend(enum_serialised_params.extra_imports)
                extra_definitions.extend(
                    enum_serialised_params.extra_definitions
                )

            continue

        # Enum types
        if inspect.isclass(value) and issubclass(value, Enum):
            params[key] = SerialisedEnumType(enum_type=value)
            extra_imports.append(Import(module="enum", target="Enum"))
            for member in value:
                type_ = type(member.value)
                module = inspect.getmodule(type_)

                if module and module != builtins:
                    module_name = module.__name__
                    extra_imports.append(
                        Import(module=module_name, target=type_.__name__)
                    )

        # Functions
        if inspect.isfunction(value):
            if value.__name__ == "<lambda>":
                raise ValueError("Lambdas can't be serialised")

            params[key] = SerialisedCallable(callable_=value)
            extra_imports.append(
                Import(module=value.__module__, target=value.__name__)
            )
            continue

        # Lazy imports - we need to resolve these now, in case the target
        # table class gets deleted in the future.
        if isinstance(value, LazyTableReference):
            table_type = value.resolve()
            params[key] = SerialisedCallable(callable_=table_type)
            extra_definitions.append(
                SerialisedTableType(table_type=table_type)
            )
            extra_imports.append(
                Import(module=Table.__module__, target="Table")
            )
            continue

        # Replace any Table class values into class and table names
        if inspect.isclass(value) and issubclass(value, Table):
            params[key] = SerialisedCallable(callable_=value)
            extra_definitions.append(SerialisedTableType(table_type=value))
            extra_imports.append(
                Import(module=Table.__module__, target="Table")
            )

            extra_imports.append(
                Import(
                    module=value._meta.primary_key.__class__.__module__,
                    target=value._meta.primary_key.__class__.__name__,
                )
            )
            # Include the extra imports and definitions required for the
            # primary column params.
            pk_serialised_params: SerialisedParams = serialise_params(
                params=value._meta.primary_key._meta.params
            )
            extra_imports.extend(pk_serialised_params.extra_imports)
            extra_definitions.extend(pk_serialised_params.extra_definitions)

            continue

        # Plain class type
        if inspect.isclass(value) and not issubclass(value, Enum):
            params[key] = SerialisedCallable(callable_=value)
            extra_imports.append(
                Import(module=value.__module__, target=value.__name__)
            )
            continue

        # All other types can remain as is.

    return SerialisedParams(
        params=params,
        extra_imports=[i for i in set(extra_imports)],
        extra_definitions=[i for i in set(extra_definitions)],
    )


def deserialise_params(params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    When reading column params from a migration file, we need to convert
    them from their serialised form.
    """
    params = deepcopy(params)

    for key, value in params.items():
        # This is purely for backwards compatibility.
        if isinstance(value, str) and not isinstance(value, Enum):
            if value != "self":
                params[key] = deserialise_legacy_params(name=key, value=value)
        elif isinstance(value, SerialisedClassInstance):
            params[key] = value.instance
        elif isinstance(value, SerialisedUUID):
            params[key] = value.instance
        elif isinstance(value, SerialisedCallable):
            params[key] = value.callable_
        elif isinstance(value, SerialisedTableType):
            params[key] = value.table_type
        elif isinstance(value, SerialisedEnumType):
            params[key] = value.enum_type
        elif isinstance(value, SerialisedEnumInstance):
            params[key] = value.instance

    return params
