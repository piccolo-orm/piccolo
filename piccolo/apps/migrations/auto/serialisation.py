from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
import datetime
from enum import Enum
import inspect
import typing as t
import uuid

from piccolo.columns.defaults.base import Default
from piccolo.table import Table

###############################################################################


@dataclass
class TableReference:
    table_class_name: str
    table_name: str

    def __hash__(self):
        return hash(f"{self.table_class_name}-{self.table_name}")

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def deserialise(self) -> t.Type[Table]:
        _Table: t.Type[Table] = type(
            self.table_class_name, (Table,), {},
        )
        _Table._meta.tablename = self.table_name
        return _Table


@dataclass
class SerialisedClass:
    instance: object

    def __hash__(self):
        return self.instance.__hash__()

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        args = ", ".join(
            [f"{key}={value}" for key, value in self.instance.__dict__.items()]
        )
        return f"{self.instance.__class__.__name__}({args})"


@dataclass
class SerialisedUUID:
    instance: uuid.UUID

    def __repr__(self):
        return f"UUID({str(self.instance)})"


###############################################################################


@dataclass
class Import:
    module: str
    target: str

    def __str__(self):
        return f"from {self.module} import {self.target}"

    def __hash__(self):
        return hash(f"{self.module}-{self.target}")

    def __lt__(self, other):
        return str(self) < str(other)


@dataclass
class SerialisedParams:
    params: t.Dict[str, t.Any]
    extra_imports: t.List[Import]


###############################################################################


def serialise_params(params: t.Dict[str, t.Any]) -> SerialisedParams:
    """
    When writing column params to a migration file, we need to serialise some
    of the values.
    """
    params = deepcopy(params)
    extra_imports: t.List[Import] = []

    for key, value in params.items():

        # Class instances
        if isinstance(value, Default):
            params[key] = SerialisedClass(instance=value)
            extra_imports.append(
                Import(
                    module=value.__class__.__module__,
                    target=value.__class__.__name__,
                )
            )
            continue

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

        # Enums
        if isinstance(value, Enum):
            # Enums already have a good __repr__.
            extra_imports.append(
                Import(
                    module=value.__module__, target=value.__class__.__name__,
                )
            )
            continue

        # Functions
        if inspect.isfunction(value):
            if value.__name__ == "<lambda>":
                raise ValueError("Lambdas can't be serialised")

            params[key] = value.__name__
            extra_imports.append(
                Import(module=value.__module__, target=value.__name__)
            )
            continue

        # Methods
        # if inspect.ismethod(value):
        #     params[key] = type

        # Replace any Table class values into class and table names
        if inspect.isclass(value) and issubclass(value, Table):
            params[key] = TableReference(
                table_class_name=value.__name__,
                table_name=value._meta.tablename,
            )
            extra_imports.append(
                Import(
                    module=TableReference.__module__, target="TableReference"
                )
            )
            continue

        # All other types can remain as is.

    return SerialisedParams(
        params=params, extra_imports=[i for i in set(extra_imports)]
    )


def deserialise_params(params: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    When reading column params from a migration file, we need to convert
    them from their serialised form.
    """
    params = deepcopy(params)

    for key, value in params.items():
        if isinstance(value, TableReference):
            params[key] = value.deserialise()
        elif isinstance(value, SerialisedClass):
            params[key] = value.instance

    return params
