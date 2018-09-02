import typing

from .columns import Column
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
        Automatically populate the tablename, and columns.
        """
        model = super().__new__(cls, name, bases, namespace)

        tablename = namespace.get('tablename')
        if not tablename:
            model.tablename = _camel_to_snake(name)

        columns = []
        for key, value in namespace.items():
            if issubclass(type(value), Column):
                columns.append(value)
                value.name = key

        model.columns = columns
        return model


class Model(metaclass=ModelMeta):

    @classmethod
    def select(cls, *column_names: [str]) -> Query:
        """
        Needs to be a simple wrapper.

        One thing I *might* want to do is have an AS string, or just allow
        that in the string. For example, 'foo as bar'. I think I'll make
        it more explicit. So you do As('foo', 'bar'). So we can easily
        inspect that the column exists, and what we're trying to map it
        to doesn't already exist.
        """
        if len(column_names) == 0:
            columns_str = '*'
        else:
            # TODO - make sure the columns passed in are valid
            columns_str = ', '.join(column_names)

        return Query(
            type='SELECT',
            model=cls,
            base=f'SELECT {columns_str} from {cls.tablename}'
        )

    @classmethod
    def insert(cls, *instances: ['Model']):
        """
        In typing is it possible to distinguish between a class and a class
        instance?

        Pokemon.insert(
            Pokemon(name="jigglypuff", power=500, trainer="florence")
        )

        Need to allow things like:

        jigglypuff = Pokemon(name="jigglypuff", power=500, trainer="florence")

        Pokemon.insert(jigglypuff)

        jigglypuff.power = 600
        # this is where save would be useful ...
        # save could be an alias to self.__cls__.save(self)
        # it just depends if the instance has an id set yet
        # if no id, use self.__cls__.insert(self)
        # if an id, use self.__cls__.update(**self.columns)

        It depends how far wen want to go with ORM style
        -> need to avoid properties which trigger ORM queries
        --> dot lookups should just return the id
        ---> can do Pokemon.get_related('gym')
        -> makes related queries tricky
        -> I need to start building apps using aragorm ... so can work out
        what's required and what isn't.
        -> need a simple router ...
        --> sanic or quart

        """
        pass

    @classmethod
    def update(cls, **columns):
        """
        await Pokemon.update(name='raichu').where(Pokemon.name='pikachu').execute()

        UPDATE pokemon SET name = 'raichu', power = '1000' where name = 'pikachu'
        """
        columns_str = ','.join([
            f'{column} = {getattr(cls, column).format_value(value)}' for column, value in columns.items()
        ])

        return Query(
            type='UPDATE',
            model=cls,
            base=f'UPDATE {cls.tablename} SET {columns_str}'
        )

    @classmethod
    def delete(cls, **columns):
        """
        await Pokemon.delete().where(Pokemon.name='weedle').execute()

        DELETE FROM pokemon where name = 'weedle'
        """
        return Query(
            type='DELETE',
            model=cls,
            base=f'DELETE FROM {cls.tablename}'
        )

    @classmethod
    def create(cls):
        """
        await Pokemon.create().execute()
        """
        return Query(
            type='CREATE',
            model=cls,
            base=f'CREATE TABLE {cls.tablename}'
        )
