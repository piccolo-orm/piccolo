import asyncio
import typing as t

from piccolo.apps.schema.commands.generate import get_output_schema
from piccolo.table import Table, TableMetaclass


class Immutable(object):
    def _immutable(self, *arg, **kw) -> TypeError:
        raise TypeError("%s object is immutable" % self.__class__.__name__)

    __delitem__ = __setitem__ = __setattr__ = _immutable


class ImmutableDict(Immutable, dict):
    """A dictionary that is not publicly mutable."""

    clear = pop = popitem = setdefault = update = Immutable._immutable

    def __new__(cls, *args):
        new = dict.__new__(cls)
        return new

    def copy(self):
        raise NotImplementedError(
            "an immutabledict shouldn't need to be copied.  use dict(d) "
            "if you need a mutable dictionary."
        )

    def __reduce__(self):
        return ImmutableDict, (dict(self),)

    def _insert_item(self, key, value) -> None:
        """
        insert an item into the dictionary directly.
        """
        dict.__setitem__(self, key, value)

    def _delete_item(self, key) -> None:
        """
        Delete an item from dictionary directly.
        """
        dict.__delitem__(self, key)

    def __repr__(self):
        return f"ImmutableDict({dict.__repr__(self)})"


class Singleton(type):
    """
    A metaclass that creates a Singleton base class when called.
    """

    _instances: t.Dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class TableStorage(metaclass=Singleton):
    """
    A singleton object to store reflected tables
    """

    def __init__(self):
        self.tables = ImmutableDict()

    async def reflect(
        self,
        schema_name: str = "public",
        if_not_exists: t.Optional[bool] = False,
    ) -> None:
        output_schema = await get_output_schema(schema_name=schema_name)
        add_tables = [
            self._add_table(
                schema_name=schema_name,
                table=table,
                if_not_exists=if_not_exists,
            )
            for table in output_schema.tables
        ]
        await asyncio.gather(*add_tables)

    async def _add_table(
        self,
        schema_name: str,
        table: t.Type[Table],
        if_not_exists: t.Optional[bool] = False,
    ) -> None:
        if isinstance(table, TableMetaclass):
            tablename = self._get_table_name(
                table._meta.tablename, schema_name
            )
            if if_not_exists:
                if self.tables.get(tablename):
                    return
            self.tables._insert_item(tablename, table)

    @staticmethod
    def _get_table_name(name: str, schema: str):
        if schema == "public":
            return name
        else:
            return schema + "." + name

    def __repr__(self):
        return f"{self.tables}"
