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
    def __init__(self, table: 'Table', column_names: t.List[str]) -> None:
        self.column_names = column_names
        super().__init__(table=table, base='')

    def __str__(self):
        if len(self.column_names) == 0:
            columns_str = '*'
        else:
            # TODO - make sure the columns passed in are valid
            columns_str = ', '.join(self.column_names)

        select = 'SELECT DISTINCT' if self.distinct else 'SELECT'
        query = f'{select} {columns_str} FROM "{self.table.Meta.tablename}"'

        #######################################################################

        # JOIN
        for column_name in self.column_names:
            if '.' in column_name:
                local_name, _ = column_name.split('.')
                table_name = self.table.get_column_by_name(
                    local_name
                ).references.Meta.tablename
                query += (
                    f' JOIN {table_name} ON {local_name} = {table_name}.id'
                )

        #######################################################################

        if self._where:
            query += f' WHERE {self._where.__str__()}'

        if self._order_by:
            query += self._order_by.__str__()

        if self._limit:
            query += self._limit.__str__()

        if self._count:
            query = f'SELECT COUNT(*) FROM ({query}) AS sub_query'

        return query


class Objects(
    Query,
    LimitMixin,
    OrderByMixin,
    WhereMixin,
):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    _output = Output(as_objects=True)

    def __str__(self):
        """
        Need to do this without repeating select ...
        """
        select = Select(
            table=self.table,
            column_names=[]
        )

        for attr in ('_limit', '_where', '_output', 'order_by'):
            setattr(select, attr, getattr(self, attr))

        return select.__str__()


class Insert(Query, AddMixin):

    def run_callback(self, results):
        for index, row in enumerate(results):
            self._add[index].id = row['id']

    def __str__(self):
        base = f'INSERT INTO "{self.table.Meta.tablename}"'
        columns = ','.join(
            [i.name for i in self.table.Meta.columns]
        )
        values = ','.join(
            i.__str__() for i in self._add
        )
        query = f'{base} ({columns}) VALUES {values} RETURNING id'
        return query


class Delete(Query, WhereMixin):

    def __str__(self):
        query = f'DELETE FROM {self.table.Meta.tablename}'
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        return query


class Create(Query):
    """
    Creates a database table.
    """

    def __str__(self):
        base = f'CREATE TABLE "{self.table.Meta.tablename}"'
        columns = ', '.join([i.__str__() for i in self.table.Meta.columns])
        query = f'{base} ({columns})'
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


class Drop(Query):

    def __str__(self):
        return f'DROP TABLE "{self.table.Meta.tablename}"'


class TableExists(Query):

    def response_handler(self, response):
        return response[0]['exists']

    def __str__(self):
        return (
            "SELECT EXISTS(SELECT * FROM information_schema.tables WHERE "
            f"table_name = '{self.table.Meta.tablename}')"
        )


class Exists(Query, WhereMixin):

    def __str__(self):
        select = Select(
            self.table,
            f'SELECT * FROM {self.table.Meta.tablename}'
        )
        select._where = self._where
        subquery = select.__str__()
        return f'SELECT EXISTS({subquery})'
