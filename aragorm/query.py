import asyncpg

from .fields import And, Where
from .types import Combinable



TEST_CREDENTIALS = {
    'host': 'localhost',
    'database': 'aragorm',
    'user': 'aragorm',
    'password': 'aragorm'
}


class Value(object):
    """
    This needs to have a type, which needs to be compatible with the field
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
    def __init__(self, field_name: str):
        self.field_name = field_name

    def __str__(self):
        return f' ORDER BY {self.field_name}'


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

    def _is_valid_field_name(self, field_name: str):
        if field_name.startswith('-'):
            field_name = field_name[1:]
        return field_name in [i.name for i in self.model.fields]

    def order_by(self, field_name: str):
        if not self._is_valid_field_name(field_name):
            raise ValueError(f"{field_name} isn't a valid field name")
        self._order_by = OrderBy(field_name)
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
