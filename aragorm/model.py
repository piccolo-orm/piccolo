import typing

from .fields import Field
from .query import Query
from .utils import _camel_to_snake


class Database(object):

    async def execute(*queries):
        """
        Use asyncio.gather here ...
        """
        pass


class ModelMeta(type):

    def __new__(cls, name, bases, namespace, **kwds):
        """
        Automatically populate the tablename, and fields.
        """
        model = super().__new__(cls, name, bases, namespace)

        tablename = namespace.get('tablename')
        if not tablename:
            model.tablename = _camel_to_snake(name)

        fields = []
        for key, value in namespace.items():
            if issubclass(type(value), Field):
                fields.append(value)
                value.name = key

        model.fields = fields
        return model


class Model(metaclass=ModelMeta):

    @classmethod
    def select(cls, *field_names: [str]) -> Query:
        """
        Needs to be a simple wrapper.

        One thing I *might* want to do is have an AS string, or just allow
        that in the string. For example, 'foo as bar'. I think I'll make
        it more explicit. So you do As('foo', 'bar'). So we can easily
        inspect that the field exists, and what we're trying to map it
        to doesn't already exist.
        """
        if len(field_names) == 0:
            fields_str = '*'
        else:
            # TODO - make sure the fields passed in are valid
            fields_str = ', '.join(field_names)

        return Query(
            type='SELECT',
            model=cls,
            base=f'SELECT {fields_str} from {cls.tablename}'
        )

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
