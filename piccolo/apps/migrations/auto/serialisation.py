from __future__ import annotations

import abc
import builtins
import datetime
import decimal
import inspect
import typing as t
import uuid
import warnings
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


class CanConflictWithGlobalNames(abc.ABC):
    @abc.abstractmethod
    def warn_if_is_conflicting_with_global_name(self):
        ...


class UniqueGlobalNamesMeta(type):
    """
    Metaclass for ``UniqueGlobalNames``.

    Fulfills the following functions:

    - Assure that no two class attributes have the same value.
    - Add class attributes `COLUMN_<capitalized column class name>`
      to the class for each column type.
    """

    def __new__(mcs, name, bases, class_attributes):
        class_attributes_with_columns = mcs.merge_class_attributes(
            class_attributes,
            mcs.get_column_class_attributes(),
        )

        return super().__new__(
            mcs,
            name,
            bases,
            mcs.merge_class_attributes(
                class_attributes_with_columns,
                {
                    "unique_names": mcs.get_unique_class_attribute_values(
                        class_attributes_with_columns
                    )
                },
            ),
        )

    @staticmethod
    def get_unique_class_attribute_values(
        class_attributes: t.Dict[str, t.Any]
    ) -> t.Set[t.Any]:
        """
        Return class attribute values.

        Raises an error if attribute values are not unique.
        """

        unique_attribute_values = set()
        for attribute_name, attribute_value in class_attributes.items():
            # Skip special attributes, i.e. "__<special attribute name>__"
            if attribute_name.startswith("__") and attribute_name.endswith(
                "__"
            ):
                continue

            if attribute_value in unique_attribute_values:
                raise ValueError(
                    f"Duplicate unique global name {attribute_value}"
                )
            unique_attribute_values.add(attribute_value)

        return unique_attribute_values

    @staticmethod
    def merge_class_attributes(
        class_attributes1: t.Dict[str, t.Any],
        class_attributes2: t.Dict[str, t.Any],
    ) -> t.Dict[str, t.Any]:
        """
        Merges two class attribute dictionaries.

        Raise an error if both dictionaries have an attribute
        with the same name.
        """

        for attribute_name in class_attributes2:
            if attribute_name in class_attributes1:
                raise ValueError(f"Duplicate class attribute {attribute_name}")

        return dict(**class_attributes1, **class_attributes2)

    @staticmethod
    def get_column_class_attributes() -> t.Dict[str, str]:
        """Automatically generates global names for each column type."""

        import piccolo.columns.column_types

        class_attributes: t.Dict[str, str] = {}
        for module_global in piccolo.columns.column_types.__dict__.values():
            try:
                if module_global is not Column and issubclass(
                    module_global, Column
                ):
                    class_attributes[
                        f"COLUMN_{module_global.__name__.upper()}"
                    ] = module_global.__name__
            except TypeError:
                pass

        return class_attributes


class UniqueGlobalNames(metaclass=UniqueGlobalNamesMeta):
    """
    Contains global names that may be used during serialisation.

    The global names are stored as class attributes. Names that may
    occur in the global namespace after serialisation should be listed here.

    This class is meant to prevent against the use of conflicting global
    names. If possible imports and global definitions should use this
    class to ensure that no conflicts arise during serialisation.
    """

    # Piccolo imports
    TABLE = Table.__name__
    DEFAULT = Default.__name__
    # Column types are omitted because they are added by metaclass

    # Standard library imports
    STD_LIB_ENUM = Enum.__name__
    STD_LIB_MODULE_DECIMAL = "decimal"

    # Third-party library imports
    EXTERNAL_MODULE_UUID = "uuid"
    EXTERNAL_UUID = f"{EXTERNAL_MODULE_UUID}.{uuid.UUID.__name__}"

    # This attribute is set in metaclass
    unique_names: t.Set[str]

    @classmethod
    def warn_if_is_conflicting_name(
        cls, name: str, name_type: str = "Name"
    ) -> None:
        """Raise an error if ``name`` matches a class attribute value."""

        if cls.is_conflicting_name(name):
            warnings.warn(
                f"{name_type} '{name}' could conflict with global name",
                UniqueGlobalNameConflictWarning,
            )

    @classmethod
    def is_conflicting_name(cls, name: str) -> bool:
        """Check if ``name`` matches a class attribute value."""

        return name in cls.unique_names

    @staticmethod
    def warn_if_are_conflicting_objects(
        objects: t.Iterable[CanConflictWithGlobalNames],
    ) -> None:
        """
        Call each object's ``raise_if_is_conflicting_with_global_name`` method.
        """

        for obj in objects:
            obj.warn_if_is_conflicting_with_global_name()


class UniqueGlobalNameConflictWarning(UserWarning):
    pass


###############################################################################


@dataclass
class Import(CanConflictWithGlobalNames):
    module: str
    target: t.Optional[str] = None
    expect_conflict_with_global_name: t.Optional[str] = None

    def __post_init__(self) -> None:
        if (
            self.expect_conflict_with_global_name is not None
            and not UniqueGlobalNames.is_conflicting_name(
                self.expect_conflict_with_global_name
            )
        ):
            raise ValueError(
                f"`expect_conflict_with_global_name="
                f'"{self.expect_conflict_with_global_name}"` '
                f"is not listed in `{UniqueGlobalNames.__name__}`"
            )

    def __repr__(self):
        if self.target is None:
            return f"import {self.module}"

        return f"from {self.module} import {self.target}"

    def __hash__(self):
        if self.target is None:
            return hash(f"{self.module}")

        return hash(f"{self.module}-{self.target}")

    def __lt__(self, other):
        return repr(self) < repr(other)

    def warn_if_is_conflicting_with_global_name(self):
        name = self.module if self.target is None else self.target
        if name == self.expect_conflict_with_global_name:
            return

        if UniqueGlobalNames.is_conflicting_name(name):
            UniqueGlobalNames.warn_if_is_conflicting_name(
                name, name_type="Import"
            )


class Definition(CanConflictWithGlobalNames, abc.ABC):
    @abc.abstractmethod
    def __repr__(self):
        ...

    ###########################################################################
    # To allow sorting:

    def __lt__(self, value):
        return self.__repr__() < value.__repr__()

    def __le__(self, value):
        return self.__repr__() <= value.__repr__()

    def __gt__(self, value):
        return self.__repr__() > value.__repr__()

    def __ge__(self, value):
        return self.__repr__() >= value.__repr__()


@dataclass
class SerialisedParams:
    params: t.Dict[str, t.Any]
    extra_imports: t.List[Import]
    extra_definitions: t.List[Definition] = field(default_factory=list)


###############################################################################


def check_equality(self, other):
    if getattr(other, "__hash__", None) is not None:
        return self.__hash__() == other.__hash__()
    else:
        return False


@dataclass
class SerialisedBuiltin:
    builtin: t.Any

    def __hash__(self):
        return hash(self.builtin.__name__)

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        return self.builtin.__name__


@dataclass
class SerialisedClassInstance:
    instance: object

    def __hash__(self):
        return self.instance.__hash__()

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        return repr_class_instance(self.instance)


@dataclass
class SerialisedColumnInstance:
    instance: Column
    serialised_params: SerialisedParams

    def __hash__(self):
        return self.instance.__hash__()

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        args = ", ".join(
            f"{key}={self.serialised_params.params.get(key).__repr__()}"
            for key in self.instance._meta.params.keys()
        )

        return f"{self.instance.__class__.__name__}({args})"


@dataclass
class SerialisedEnumInstance:
    instance: Enum

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        return f"{self.instance.__class__.__name__}.{self.instance.name}"


@dataclass
class SerialisedTableType(Definition):
    table_type: t.Type[Table]

    def __hash__(self):
        return hash(
            f"{self.table_type._meta.tablename}-{self.table_type.__name__}"
        )

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        tablename = self.table_type._meta.tablename

        # We have to add the primary key column definition too, so foreign
        # keys can be created with the correct type.
        pk_column = self.table_type._meta.primary_key
        pk_column_name = pk_column._meta.name
        serialised_pk_column = SerialisedColumnInstance(
            pk_column,
            serialised_params=serialise_params(params=pk_column._meta.params),
        )

        #######################################################################

        # When creating a ForeignKey, the user can specify a column other than
        # the primary key to reference.
        serialised_target_columns: t.Set[SerialisedColumnInstance] = set()

        for fk_column in self.table_type._meta._foreign_key_references:
            target_column = fk_column._foreign_key_meta.target_column
            if target_column is None:
                # Just references the primary key
                continue
            elif type(target_column) is str:
                column = self.table_type._meta.get_column_by_name(
                    target_column
                )
            elif isinstance(target_column, Column):
                column = self.table_type._meta.get_column_by_name(
                    target_column._meta.name
                )
            else:
                raise ValueError("Unrecognised `target_column` value.")

            serialised_target_columns.add(
                SerialisedColumnInstance(
                    column,
                    serialised_params=serialise_params(
                        params=column._meta.params
                    ),
                )
            )

        #######################################################################

        definition = (
            f"class {self.table_class_name}"
            f'({UniqueGlobalNames.TABLE}, tablename="{tablename}"): '
            f"{pk_column_name} = {serialised_pk_column}"
        )

        for serialised_target_column in serialised_target_columns:
            definition += f"; {serialised_target_column.instance._meta.name} = {serialised_target_column}"  # noqa: E501

        return definition

    def __lt__(self, other):
        return repr(self) < repr(other)

    @property
    def table_class_name(self) -> str:
        return self.table_type.__name__

    def warn_if_is_conflicting_with_global_name(self) -> None:
        UniqueGlobalNames.warn_if_is_conflicting_name(self.table_class_name)


@dataclass
class SerialisedEnumType:
    enum_type: t.Type[Enum]

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        class_name = self.enum_type.__name__
        params = {i.name: i.value for i in self.enum_type}
        return f"{UniqueGlobalNames.STD_LIB_ENUM}('{class_name}', {params})"


@dataclass
class SerialisedCallable:
    callable_: t.Callable

    def __hash__(self):
        return hash(self.callable_.__name__)

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        return self.callable_.__name__


@dataclass
class SerialisedUUID:
    instance: uuid.UUID

    def __hash__(self):
        return self.instance.int

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        return f'{UniqueGlobalNames.EXTERNAL_UUID}("{str(self.instance)}")'


@dataclass
class SerialisedDecimal:
    instance: decimal.Decimal

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        return check_equality(self, other)

    def __repr__(self):
        return f"{UniqueGlobalNames.STD_LIB_MODULE_DECIMAL}." + repr(
            self.instance
        ).replace("'", '"')


###############################################################################


def serialise_params(params: t.Dict[str, t.Any]) -> SerialisedParams:
    """
    When writing column params to a migration file, we need to serialise some
    of the values.
    """
    params = deepcopy(params)
    extra_imports: t.List[Import] = []
    extra_definitions: t.List[Definition] = []

    for key, value in params.items():

        # Builtins, such as str, list and dict.
        if inspect.getmodule(value) == builtins:
            params[key] = SerialisedBuiltin(builtin=value)
            continue

        # Column instances
        if isinstance(value, Column):

            # For target_column (which is used by ForeignKey), we can just
            # serialise it as the column name:
            if key == "target_column":
                params[key] = value._meta.name
                continue

            ###################################################################

            # For Array definitions, we want to serialise the full column
            # definition:

            column: Column = value
            serialised_params: SerialisedParams = serialise_params(
                params=column._meta.params
            )

            # Include the extra imports and definitions required for the
            # column params.
            extra_imports.extend(serialised_params.extra_imports)
            extra_definitions.extend(serialised_params.extra_definitions)

            column_class_name = column.__class__.__name__
            extra_imports.append(
                Import(
                    module=column.__class__.__module__,
                    target=column_class_name,
                    expect_conflict_with_global_name=getattr(
                        UniqueGlobalNames,
                        f"COLUMN_{column_class_name.upper()}",
                        None,
                    ),
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
                    expect_conflict_with_global_name=UniqueGlobalNames.DEFAULT,
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
            extra_imports.append(
                Import(
                    module=UniqueGlobalNames.EXTERNAL_MODULE_UUID,
                    expect_conflict_with_global_name=(
                        UniqueGlobalNames.EXTERNAL_MODULE_UUID
                    ),
                )
            )
            continue

        # Decimals
        if isinstance(value, decimal.Decimal):
            params[key] = SerialisedDecimal(instance=value)
            extra_imports.append(
                Import(
                    module=UniqueGlobalNames.STD_LIB_MODULE_DECIMAL,
                    expect_conflict_with_global_name=(
                        UniqueGlobalNames.STD_LIB_MODULE_DECIMAL
                    ),
                )
            )
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
            extra_imports.append(
                Import(
                    module="enum",
                    target=UniqueGlobalNames.STD_LIB_ENUM,
                    expect_conflict_with_global_name=(
                        UniqueGlobalNames.STD_LIB_ENUM
                    ),
                )
            )
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
                Import(
                    module=Table.__module__,
                    target=UniqueGlobalNames.TABLE,
                    expect_conflict_with_global_name=UniqueGlobalNames.TABLE,
                )
            )
            continue

        # Replace any Table class values into class and table names
        if inspect.isclass(value) and issubclass(value, Table):
            params[key] = SerialisedCallable(callable_=value)
            extra_definitions.append(SerialisedTableType(table_type=value))
            extra_imports.append(
                Import(
                    module=Table.__module__,
                    target=UniqueGlobalNames.TABLE,
                    expect_conflict_with_global_name=UniqueGlobalNames.TABLE,
                )
            )

            primary_key_class = value._meta.primary_key.__class__
            extra_imports.append(
                Import(
                    module=primary_key_class.__module__,
                    target=primary_key_class.__name__,
                    expect_conflict_with_global_name=getattr(
                        UniqueGlobalNames,
                        f"COLUMN_{primary_key_class.__name__.upper()}",
                        None,
                    ),
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

    unique_extra_imports = list(set(extra_imports))
    UniqueGlobalNames.warn_if_are_conflicting_objects(unique_extra_imports)

    unique_extra_definitions = list(set(extra_definitions))
    UniqueGlobalNames.warn_if_are_conflicting_objects(unique_extra_definitions)

    return SerialisedParams(
        params=params,
        extra_imports=unique_extra_imports,
        extra_definitions=unique_extra_definitions,
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
        elif isinstance(value, SerialisedDecimal):
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
