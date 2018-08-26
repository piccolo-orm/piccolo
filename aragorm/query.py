import asyncpg

from .fields import Where


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

    where_clauses: [Where] = []

    def __init__(self, type: str, model: 'Model', base: str):
        """
        A query has to be a certain type.
        """
        # For example select * from my_table
        self.base = base
        self.model = model

    def generate_query(self):
        """
        For each where clause ... need to get the name ...

        The query needs a link to the table calling it ...
        """
        return self.base

    async def execute(self, as_dict=True) -> str:
        """
        Now ... just execute it from within here for now ...
        """
        conn = await asyncpg.connect(**TEST_CREDENTIALS)
        results = await conn.fetch(self.generate_query())
        await conn.close()
        # TODO Be able to output it in different formats.
        return dict(results[0].items())

    def where(self, where: Where):
        """
        Just appends where clauses ...
        """
        self.where_clauses.append(where)
        return self

    def __str__(self):
        return self.generate_query()
