import asyncpg

from .columns import And, Where
from .types import Combinable



TEST_CREDENTIALS = {
    'host': 'localhost',
    'database': 'aragorm',
    'user': 'aragorm',
    'password': 'aragorm'
}


class Value(object):
    """
    This needs to have a type, which needs to be compatible with the column
    type.
    """
    pass


class Limit():
    def __init__(self, number: int):
        if type(number) != int:
            raise TypeError('Limit must be an integer')
        self.number = number

    def __str__(self):
        return f' LIMIT {self.number}'


class OrderBy:
    def __init__(self, column_name: str, ascending: bool):
        self.column_name = column_name
        self.ascending = ascending

    def __str__(self):
        order = 'ASC' if self.ascending else 'DESC'
        return f' ORDER BY {self.column_name} {order}'


class Query(object):
    """
    For now, just make it handle select.
    """

    valid_types = ['INSERT', 'UPDATE', 'SELECT']

    def __init__(self, type: str, model: 'Model', base: str):
        """
        A query has to be a certain type.
        """
        # For example select * from my_table
        self.base = base
        self.model = model
        self._where: [Combinable] = None
        self._limit: Limit = None
        self._order_by: OrderBy = None

    # TODO - I want sync and async versions of this
    async def execute(self, as_dict=True):
        """
        Now ... just execute it from within here for now ...
        """
        conn = await asyncpg.connect(**TEST_CREDENTIALS)
        results = await conn.fetch(self.__str__())
        await conn.close()
        # TODO Be able to output it in different formats.
        return [dict(i.items()) for i in results]

    def where(self, where: Combinable):
        if self._where:
            self._where = And(self._where, where)
        else:
            self._where = where
        return self

    def limit(self, number: int):
        self._limit = Limit(number)
        return self

    def first(self):
        self._limit = Limit(1)
        return self

    def count(self):
        self.base = f'SELECT COUNT(*) FROM {self.model.tablename}'
        return self

    def _is_valid_column_name(self, column_name: str):
        if column_name.startswith('-'):
            column_name = column_name[1:]
        if not column_name in [i.name for i in self.model.columns]:
            raise ValueError(f"{column_name} isn't a valid column name")

    def order_by(self, column_name: str):
        self._is_valid_column_name(column_name)

        ascending = True
        if column_name.startswith('-'):
            ascending = False
            column_name = column_name[1:]

        self._order_by = OrderBy(column_name, ascending)
        return self

    def __str__(self):
        query = self.base
        if self._where:
            query += f' WHERE {self._where.__str__()}'
        if self._order_by:
            query += self._order_by.__str__()
        if self._limit:
            query += self._limit.__str__()
        print(query)
        return query
