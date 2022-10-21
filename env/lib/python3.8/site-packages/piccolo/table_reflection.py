"""
This is an advanced Piccolo feature which allows runtime reflection of database
tables.
"""

import asyncio
import typing as t
from dataclasses import dataclass

from piccolo.apps.schema.commands.generate import get_output_schema
from piccolo.table import Table


class Immutable(object):
    def _immutable(self, *args, **kwargs) -> TypeError:
        raise TypeError("%s object is immutable" % self.__class__.__name__)

    __delitem__ = __setitem__ = __setattr__ = _immutable  # type: ignore


class ImmutableDict(Immutable, dict):  # type: ignore
    """A dictionary that is not publicly mutable."""

    clear = pop = popitem = setdefault = update = Immutable._immutable  # type: ignore  # noqa: E501

    def __new__(cls, *args):
        return dict.__new__(cls)

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


@dataclass
class TableNameDetail:
    name: str = ""
    schema: str = ""


class TableStorage(metaclass=Singleton):
    """
    A singleton object to store and access reflected tables. Currently it just
    works with Postgres.
    """

    def __init__(self):
        self.tables = ImmutableDict()
        self._schema_tables = {}

    async def reflect(
        self,
        schema_name: str = "public",
        include: t.Union[t.List[str], str, None] = None,
        exclude: t.Union[t.List[str], str, None] = None,
        keep_existing: bool = False,
    ) -> None:
        """
        Imports tables from the database into ``Table`` objects without
        hard-coding them.

        If a table has a reference to another table, the referenced table will
        be imported too. Reflection can have a performance impact based on the
        number of tables.

        If you want to reflect your whole database, make sure to only do it
        once or use the provided parameters instead of reflecting the whole
        database every time.

        :param schema_name:
            Name of the schema you want to reflect.
        :param include:
            It will only reflect the specified tables. Can be a list of tables
            or a single table.
        :param exclude:
            It won't reflect the specified tables. Can be a list of tables or
            a single table.
        :param keep_existing:
            If True, it will exclude the available tables and reflects the
            currently unavailable ones. Default is False.
        :returns:
            None

        """
        include_list = self._to_list(include)
        exclude_list = self._to_list(exclude)

        if keep_existing:
            exclude += self._schema_tables.get(schema_name, [])

        output_schema = await get_output_schema(
            schema_name=schema_name, include=include_list, exclude=exclude_list
        )
        add_tables = [
            self._add_table(schema_name=schema_name, table=table)
            for table in output_schema.tables
        ]
        await asyncio.gather(*add_tables)

    def clear(self) -> None:
        """
        Removes all the tables within ``TableStorage``.

        :returns:
            None

        """
        dict.clear(self.tables)
        self._schema_tables.clear()

    async def get_table(self, tablename: str) -> t.Optional[t.Type[Table]]:
        """
        Returns the ``Table`` class if it exists. If the table is not present
        in ``TableStorage``, it will try to reflect it.

        :param tablename:
            The name of the table, schema name included. If the schema is
            public, it's not necessary. For example: "public.manager" or
            "manager", "test_schema.test_table".
        :returns:
            Table | None

        """
        table_class = self.tables.get(tablename)
        if table_class is None:
            tableNameDetail = self._get_schema_and_table_name(tablename)
            await self.reflect(
                schema_name=tableNameDetail.schema,
                include=[tableNameDetail.name],
            )
            table_class = self.tables.get(tablename)
        return table_class

    async def _add_table(self, schema_name: str, table: t.Type[Table]) -> None:
        if issubclass(table, Table):
            table_name = self._get_table_name(
                table._meta.tablename, schema_name
            )
            self.tables._insert_item(table_name, table)
            self._add_to_schema_tables(
                schema_name=schema_name, table_name=table._meta.tablename
            )

    def _add_to_schema_tables(self, schema_name: str, table_name: str) -> None:
        """
        We keep record of schemas and their tables for easy use. This method
        adds a table to its schema.

        """
        schema_tables = self._schema_tables.get(schema_name)
        if schema_tables is None:
            self._schema_tables[schema_name] = []
        else:
            self._schema_tables[schema_name].append(table_name)

    @staticmethod
    def _get_table_name(name: str, schema: str):
        return name if schema == "public" else f"{schema}.{name}"

    def __repr__(self):
        return f"{[tablename for tablename, _ in self.tables.items()]}"

    @staticmethod
    def _get_schema_and_table_name(tablename: str) -> TableNameDetail:
        """
        Extract schema name and table name from full name of the table.

        :param tablename:
            The full name of the table.
        :returns:
            Returns the name of the schema and the table.

        """
        tablename_list = tablename.split(".")
        if len(tablename_list) == 2:
            return TableNameDetail(
                name=tablename_list[1], schema=tablename_list[0]
            )

        elif len(tablename_list) == 1:
            return TableNameDetail(name=tablename_list[0], schema="public")
        else:
            raise ValueError("Couldn't find schema name.")

    @staticmethod
    def _to_list(value: t.Any) -> t.List:
        if isinstance(value, list):
            return value
        elif isinstance(value, (tuple, set)):
            return list(value)
        elif isinstance(value, str):
            return [value]
        return []
