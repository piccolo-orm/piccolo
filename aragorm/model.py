import typing

from fields import Field


class Database(object):

    async def execute(*queries):
        """
        Use asyncio.gather here ...
        """
        pass


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

    valid_types = ['INSERT', 'UPDATE', 'SELECT']

    where_clauses: [Where] = []

    def __init__(self, type: str):
        """
        A query has to be a certain type. Currently:
        """
        pass

    async def execute(self):
        pass

    def where(self):
        """

        """
        pass


class Model(object):

    @property
    def fields() -> [Field]:
        """
        Needs to inspect the subclass, and return all Fields.

        Also ... needs to be a classproperty, or just stored by the meta
        class.

        Want this generated once by the meta class, or cached.
        """

    @classmethod
    async def select(cls, *field_names: [str]) -> Query:
        """
        Needs to be a simple wrapper.

        One thing I *might* want to do is have an AS string, or just allow
        that in the string. For example, 'foo as bar'. I think I'll make
        it more explicit. So you do As('foo', 'bar'). So we can easily
        inspect that the field exists, and what we're trying to map it
        too doesn't already exist.
        """
        if '*' in field_names:
            field_names = '*'

        fields_str = ', '.join(field_names)

        # TODO - make sure the fields passed in are valid

        query = f'SELECT {fields_str} from {cls.tablename}'
        pass

    @classmethod
    async def insert(cls, *row: ["Model"]):
        """
        In typing is it possible to distinguish between a class and a class
        instance?
        """
        pass

    @classmethod
    async def update(cls):
        """
        All I want here is some filtering ... like by id, or name.

        I want to just update certain fields ...

        Need to think about the cleanest API.

        await Pokemon.update('name', 'raichu').where('name', 'pikachu').execute()

        OR:
        await Pokemon.update(name='raichu').where(name='pikachu').execute()

        await Pokemon.select('name').where(color='yellow').execute()

        OR:
        await Pokemon.select('name', 'power').where(power='yellow').execute()

        Is there any way to use > symbol???
        """
        pass
