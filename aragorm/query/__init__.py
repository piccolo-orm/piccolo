import typing as t

from .base import Query
from .mixins import (
    AddMixin,
    CountMixin,
    DistinctMixin,
    LimitMixin,
    OrderByMixin,
    OutputMixin,
    WhereMixin,
    Output
)
if t.TYPE_CHECKING:
    from table import Table  # noqa


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
        self._output = Output(as_objects=True)
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
