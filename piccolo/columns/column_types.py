from __future__ import annotations
import copy
from datetime import datetime
import typing as t
import uuid

from piccolo.columns.base import Column, ForeignKeyMeta, OnDelete, OnUpdate
from piccolo.querystring import Unquoted

if t.TYPE_CHECKING:
    from piccolo.table import Table  # noqa
    from piccolo.custom_types import Datetime  # noqa


class Varchar(Column):
    """
    Used for text when you want to import character length limits.
    """

    value_type = str

    def __init__(self, length: int = 255, default: str = "", **kwargs) -> None:
        self.length = length
        self.default = default
        kwargs.update({"length": length, "default": default})
        super().__init__(**kwargs)

    @property
    def column_type(self):
        if self.length:
            return f"VARCHAR({self.length})"
        else:
            return "VARCHAR"


class Text(Column):
    """
    Used for text when you don't want any character length limits.
    """

    value_type = str

    def __init__(self, default: str = "", **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class UUID(Column):
    """
    Represented in Postgres as a UUID field, and a Varchar field in SQLite.
    """

    value_type = t.Union[str, uuid.UUID]

    def default(self) -> str:
        return str(uuid.uuid4())

    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "UUID"
        elif engine_type == "sqlite":
            return "VARCHAR"
        raise Exception("Unrecognized engine type")


class Integer(Column):
    def __init__(self, default: int = None, **kwargs) -> None:
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Serial(Column):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


DEFAULT = Unquoted("DEFAULT")
NULL = Unquoted("null")


class PrimaryKey(Column):
    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "SERIAL"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")

    def default(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return DEFAULT
        elif engine_type == "sqlite":
            return NULL
        raise Exception("Unrecognized engine type")

    def __init__(self, **kwargs) -> None:
        kwargs.update({"primary": True, "key": True})
        super().__init__(**kwargs)


class Timestamp(Column):

    value_type = datetime

    def __init__(self, default: "Datetime" = None, **kwargs) -> None:
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Boolean(Column):

    value_type = bool

    def __init__(self, default: bool = False, **kwargs) -> None:
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class ForeignKey(Integer):
    """
    Returns an integer, representing the referenced row's ID.

        some_band.manager
        >>> 1

    Can also use it to perform joins:

        Band.select().columns(Band.manager.name)

    To get a referenced row as an object:

        User.object.where(User.id == some_band.manager)

    Or use this, which is just a proxy to the above:

        some_band.related_object('manager')

    To change the manager:

        some_band.manager = some_manager_id
        some_band.save()

    Or:
        some_band.set_related_object('manager', some_manager)

    """

    column_type = "INTEGER"

    def __init__(
        self,
        references: t.Type[Table],
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        **kwargs,
    ) -> None:
        kwargs.update({"references": references})
        super().__init__(**kwargs)
        self._foreign_key_meta = ForeignKeyMeta(
            references=references, on_delete=on_delete, on_update=on_update
        )

        # Record the reverse relationship on the target table.
        references._meta.foreign_key_references.append(self)

        # Allow columns on the referenced table to be accessed via auto
        # completion.
        for column in references._meta.columns:
            _column: Column = copy.deepcopy(column)
            setattr(self, _column._meta.name, _column)
            self._foreign_key_meta.proxy_columns.append(_column)

    def __getattribute__(self, name: str):
        """
        Returns attributes unmodified unless they're Column instances, in which
        case a copy is returned with an updated call_chain (which records the
        joins required).
        """
        # see if it has an attribute with that name ...
        # if it's asking for a foreign key ... return a copy of self ...

        try:
            value = object.__getattribute__(self, name)
        except AttributeError:
            raise AttributeError

        foreignkey_class = object.__getattribute__(self, "__class__")

        if type(value) == foreignkey_class:  # i.e. a ForeignKey
            new_column = copy.deepcopy(value)
            new_column._meta.call_chain = copy.copy(self._meta.call_chain)
            new_column._meta.call_chain.append(self)

            # We have to set limits to the call chain because Table 1 can
            # reference Table 2, which references Table 1, creating an endless
            # loop. For now an arbitrary limit is set of 10 levels deep.
            # When querying a call chain more than 10 levels deep, an error
            # will be raised. Often there are more effective ways of
            # structuring a query than joining so many tables anyway.
            if len(new_column._meta.call_chain) > 10:
                raise Exception("Call chain too long!")

            for proxy_column in self._foreign_key_meta.proxy_columns:
                try:
                    delattr(new_column, proxy_column._meta.name)
                except Exception:
                    pass

            for column in value._foreign_key_meta.references._meta.columns:
                _column: Column = copy.deepcopy(column)
                _column._meta.call_chain = copy.copy(
                    new_column._meta.call_chain
                )
                _column._meta.call_chain.append(new_column)
                if _column._meta.name == "id":
                    continue
                setattr(new_column, _column._meta.name, _column)
                self._foreign_key_meta.proxy_columns.append(_column)

            return new_column
        elif issubclass(type(value), Column):
            new_column = copy.deepcopy(value)
            new_column._meta.call_chain = copy.copy(self._meta.call_chain)
            new_column._meta.call_chain.append(self)
            return new_column
        else:
            return value
