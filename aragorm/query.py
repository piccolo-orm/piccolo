import asyncpg


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


class Where(object):
    """
    Example use case - id = 5

    Can potentially simplify things dramatically here by just accepting
    postgres where clauses directly, avoiding the need for equal, greater than
    etc syntax.
    """

    def __init__(self, field: str, value: Value):
        self.field = Field
        self.value = value


class Query(object):
    """
    For now, just make it handle select.
    """

    valid_types = ['INSERT', 'UPDATE', 'SELECT']

    where_clauses: [Where] = []

    def __init__(self, type: str, base: str):
        """
        A query has to be a certain type.
        """
        # For example select * from my_table
        self.base = base

    async def execute(self, as_dict=True) -> str:
        """
        Now ... just execute it from within here for now ...
        """
        conn = await asyncpg.connect(**TEST_CREDENTIALS)
        results = await conn.fetch(self.base)
        await conn.close()
        # TODO Be able to output it in different formats.
        return dict(results[0].items())

    def where(self):
        """
        Just appends where clauses ...
        """
        pass

    def __str__(self):
        return self.base
