import asyncio
import dataclasses
import typing as t

import asyncpg

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


###############################################################################

class Query(object):

    def __init__(self, table: 'Table', base: str = '') -> None:
        self.base = base
        self.table = table

        super().__init__()

        self._limit: t.Optional[Limit] = None
        self._order_by: t.Optional[OrderBy] = None
        self._add: t.List['Table'] = []

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

        # TODO Be able to output it in different formats.
        raw = [dict(i.items()) for i in results]

        if hasattr(self, 'run_callback'):
            self.run_callback(raw)

        return self.response_handler(raw)

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

    def order_by(self, column_name: str):
        self._is_valid_column_name(column_name)

        ascending = True
        if column_name.startswith('-'):
            ascending = False
            column_name = column_name[1:]

        self._order_by = OrderBy(column_name, ascending)
        return self


class LimitMixin():

    def limit(self, number: int):
        self._limit = Limit(number)
        return self

    def first(self):
        self._limit = Limit(1)
        self.response_handler = lambda response: response[0]
        return self


class DistinctMixin():

    def distinct(self):
        """
        Replace base with SELECT DISTINCT ... or set distinct = True ...
        """
        return self


class CountMixin():

    def count(self):
        self.base = f'SELECT COUNT(*) FROM {self.table.Meta.tablename}'
        return self


class AddMixin():

    def add(self, *instances: 'Table'):
        for instance in instances:
            if not isinstance(instance, self.table):
                raise TypeError('Incompatible type added.')
        self._add += instances
        return self


###############################################################################

# TODO I don't like this whole self.base stuff

class Select(Query, WhereMixin, LimitMixin, CountMixin, OrderByMixin):

    def __str__(self):
        query = self.base
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        if self._order_by:
            query += self._order_by.__str__()
        if self._limit:
            query += self._limit.__str__()
        return query


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
