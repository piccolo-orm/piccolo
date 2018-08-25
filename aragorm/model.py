import typing

from .fields import Field
from .query import Query


class Database(object):

    async def execute(*queries):
        """
        Use asyncio.gather here ...
        """
        pass


class Model(object):

    def _tablename(cls):
        tablename = getattr(cls, 'tablename', None)
        if tablename:
            return tablename
        else:
            # TODO - FooBar -> foo_bar
            return cls.__name__.lower()

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
        if field_names == []:
            fields_str = '*'
        else:
            # TODO - make sure the fields passed in are valid
            fields_str = ', '.join(field_names)

        tablename = cls._tablename()
        return Query(base=f'SELECT {fields_str} from {tablename}')

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
