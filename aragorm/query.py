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
        self.where_clauses: [Combinable] = []

    def first(self):
        """
        LIMIT 1 ... and only return the first row ...

        I want to think about using .limit() too ...
        """

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
        if self.where_clauses:
            self.where_clauses = And(self.where_clauses[0], where)
        else:
            self.where_clauses.append(where)
        return self

    def __str__(self):
        query = self.base
        if self.where_clauses:
            query += ' WHERE '
            for clause in self.where_clauses:
                query += clause.__str__()
        print(query)
        return query
