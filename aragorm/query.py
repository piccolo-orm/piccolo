import asyncio
import dataclasses
import itertools
import typing as t

import asyncpg
try:
    import ujson as json
except ImportError:
    import json

from .columns import And
from .types import Combinable
if t.TYPE_CHECKING:
    from table import Table  # noqa


class Value(object):
    """
    This needs to have a type, which needs to be compatible with the column
    type.
    """
    pass


class Limit():

    def __init__(self, number: int) -> None:
        if type(number) != int:
            raise TypeError('Limit must be an integer')
        self.number = number

    def __str__(self):
        return f' LIMIT {self.number}'


@dataclasses.dataclass
class OrderBy():
    column_name: str
    ascending: bool

    def __str__(self):
        order = 'ASC' if self.ascending else 'DESC'
        return f' ORDER BY {self.column_name} {order}'


@dataclasses.dataclass
class Output():
    as_json: bool = False
    as_list: bool = False


###############################################################################

class Query(object):

    def __init__(self, table: 'Table', base: str = '', *args,
                 **kwargs) -> None:
        self.base = base
        self.table = table
        super().__init__()

    async def run(self, as_dict=True, credentials=None):
        """
        Should use an engine.
        """
        if not credentials:
            credentials = getattr(self.table.Meta, 'db', None)
        if not credentials:
            raise ValueError('Table has no db defined in Meta')

        conn = await asyncpg.connect(**credentials)
        results = await conn.fetch(self.__str__())
        await conn.close()

        raw = [dict(i.items()) for i in results]

        if hasattr(self, 'run_callback'):
            self.run_callback(raw)

        # I have multiple ways of modifying the final output
        # response_handlers, and output ...
        # Might try and merge them.
        raw = self.response_handler(raw)

        output = getattr(self, '_output', None)
        if output and type(raw) is list:
            if output.as_list:
                if len(raw[0].keys()) != 1:
                    raise ValueError(
                        'Each row returned more than on value'
                    )
                else:
                    raw = list(
                        itertools.chain(*[j.values() for j in raw])
                    )
            if output.as_json:
                raw = json.dumps(raw)

        return raw

    def run_sync(self, *args, **kwargs):
        """
        A convenience method for running the coroutine synchronously.

        Might make it more sophisticated in the future, so not creating /
        tearing down connections, but instead running it in a separate
        process, and dispatching coroutines to it.
        """
        return asyncio.run(
            self.run(*args, **kwargs)
        )

    def response_handler(self, response):
        """
        Subclasses can override this to modify the raw response returned by
        the database driver.
        """
        return response

    def _is_valid_column_name(self, column_name: str):
        if column_name.startswith('-'):
            column_name = column_name[1:]
        if column_name not in [i.name for i in self.table.Meta.columns]:
            raise ValueError(f"{column_name} isn't a valid column name")


###############################################################################

class WhereMixin():

    def __init__(self):
        super().__init__()
        self._where: t.Optional[Combinable] = []

    def where(self, where: Combinable):
        if self._where:
            self._where = And(self._where, where)
        else:
            self._where = where
        return self


class OrderByMixin():

    def __init__(self):
        super().__init__()
        self._order_by: t.Optional[OrderBy] = None

    def order_by(self, column_name: str):
        self._is_valid_column_name(column_name)

        ascending = True
        if column_name.startswith('-'):
            ascending = False
            column_name = column_name[1:]

        self._order_by = OrderBy(column_name, ascending)
        return self


class LimitMixin():

    def __init__(self):
        super().__init__()
        self._limit: t.Optional[Limit] = None

    def limit(self, number: int):
        self._limit = Limit(number)
        return self

    def first(self):
        self._limit = Limit(1)
        self.response_handler = lambda response: response[0]
        return self


class DistinctMixin():

    def __init__(self):
        super().__init__()
        self._distinct: bool = False

    def distinct(self):
        self._distinct = True
        return self


class CountMixin():

    def __init__(self):
        super().__init__()
        self._count: bool = False

    def count(self):
        self._count = True
        return self


class AddMixin():

    def __init__(self):
        super().__init__()
        self._add: t.List['Table'] = []

    def add(self, *instances: 'Table'):
        for instance in instances:
            if not isinstance(instance, self.table):
                raise TypeError('Incompatible type added.')
        self._add += instances
        return self


class OutputMixin():
    """
    Example usage:

    .output(as_list=True)
    .output(as_json=True)
    .output(as_json=True, as_list=True)
    """

    def __init__(self):
        super().__init__()
        self._output = Output()

    def output(
        self,
        as_list: t.Optional[bool] = None,
        as_json: t.Optional[bool] = None
    ):
        if type(as_list) is bool:
            self._output.as_list = as_list

        if type(as_json) is bool:
            self._output.as_json = as_json

        return self


###############################################################################

# TODO I don't like this whole self.base stuff
# It really limits what's possible ...

class Select(
    Query,
    CountMixin,
    DistinctMixin,
    LimitMixin,
    OrderByMixin,
    OutputMixin,
    WhereMixin,
):
    # columns_str => columns: t.List[str]
    def __init__(self, table: 'Table', columns_str: str) -> None:
        self.columns_str = columns_str
        super().__init__(table=table, base='')

    def __str__(self):
        select = 'SELECT DISTINCT' if self.distinct else 'SELECT'
        query = f'{select} {self.columns_str} FROM "{self.table.Meta.tablename}"'

        if self._where:
            query += f' WHERE {self._where.__str__()}'
        if self._order_by:
            query += self._order_by.__str__()
        if self._limit:
            query += self._limit.__str__()
        if self._count:
            query = f'SELECT COUNT(*) FROM ({query}) AS sub_query'

        return query


# TODO try and share as much between Select and Objects as possible ...
#
class Objects(
    Query,
    LimitMixin,
    OrderByMixin,
    WhereMixin,
):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.

    Inherits almost everything except OutputMixin, Distinct, Count,
    """

    def __init__(self, table: 'Table') -> None:
        # TODO - remove base altogether
        super().__init__(table=table, base='')

    def __str__(self):
        pass


class Insert(Query, AddMixin):

    def run_callback(self, results):
        for index, row in enumerate(results):
            self._add[index].id = row['id']

    def __str__(self):
        columns = ','.join([i.name for i in self.table.Meta.columns])
        values = ','.join(i.__str__() for i in self._add)
        query = f'{self.base} ({columns}) VALUES {values} RETURNING id'
        return query


class Delete(Query, WhereMixin):

    def __str__(self):
        query = self.base
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        return query


class Create(Query):
    """
    Creates a database table.
    """

    def __str__(self):
        columns = ', '.join([i.__str__() for i in self.table.Meta.columns])
        query = f'{self.base} ({columns})'
        return query


class Update(Query, WhereMixin):

    def __str__(self):
        query = self.base
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        return query


class Raw(Query):

    def __str__(self):
        return self.base


class Drop(Raw):
    pass


class TableExists(Raw):

    def response_handler(self, response):
        return response[0]['exists']


class Exists(Query, WhereMixin):

    def __str__(self):
        select = Select(
            self.table,
            f'SELECT * FROM {self.table.Meta.tablename}'
        )
        select._where = self._where
        subquery = select.__str__()
        return f'SELECT EXISTS({subquery})'
