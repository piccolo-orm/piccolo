import copy
import inspect
import typing as t

from .alter import Alter
from .columns import Column, PrimaryKey, ForeignKey
from .query import (
    Create,
    Delete,
    Drop,
    Exists,
    Insert,
    Objects,
    Raw,
    Select,
    TableExists,
    Update,
)
from .utils import _camel_to_snake


class Database(object):

    async def run(*queries):
        """
        Use asyncio.gather here ...

        I think I'll call it Engine instead ...
        """
        pass


class TableMeta(type):

    def __new__(cls, name, bases, namespace, **kwds):
        """
        Automatically populate the tablename, and columns.
        """
        # TODO super might not be required ...
        table = super().__new__(cls, name, bases, namespace)

        Meta = namespace.get('Meta')
        tablename = getattr(Meta, 'tablename', None) if Meta else None
        if not tablename:
            table.Meta.tablename = _camel_to_snake(name)

        columns = []
        for key, value in namespace.items():
            if issubclass(type(value), Column):
                columns.append(value)
                value.name = key

        if bases:
            for base in bases:
                if hasattr(base, 'Meta'):
                    _columns = getattr(base.Meta, 'columns', None)
                    if _columns:
                        columns = _columns + columns

        table.Meta.columns = columns
        return table


class Table(metaclass=TableMeta):

    id = PrimaryKey()

    class Meta:
        tablename = None
        columns: t.List[Column] = []
        db: t.Optional[t.Dict[t.Any, t.Any]] = None

    def __init__(self, **kwargs):
        """
        TODO:
        Need to know the memory size of each instance ... can't be
        massive.
        """
        for column in self.Meta.columns:
            value = kwargs.pop(column.name, None)
            if not value:
                if column.default:
                    value = column.default() if inspect.isfunction(
                        column.default
                    ) else column.default
                else:
                    if not column.null:
                        raise ValueError(f"{column.name} wasn't provided")
            self[column.name] = value

        unrecognized = kwargs.keys()
        if unrecognized:
            raise ValueError(f'Unrecognized columns - {unrecognized}')

    def save(self):
        """
        A proxy to an insert or update query.
        """
        if not hasattr(self, 'id'):
            raise ValueError('No id value found')

        cls = self.__class__

        if type(self.id) == int:
            # pre-existing row
            kwargs = {
                i.name: getattr(self, i.name, None) for i in cls.Meta.columns
            }
            _id = kwargs.pop('id')
            return cls.update(**kwargs).where(
                cls.id == _id
            )
        else:
            return cls.insert().add(self)

    def remove(self):
        """
        A proxy to a delete query.
        """
        _id = self.id

        if type(_id) != int:
            raise ValueError('Can only delete pre-existing rows with an id.')

        self.id = None

        return self.__class__.delete().where(
            self.__class__.id == _id
        )

    def get_related(self, column_name: str):
        """
        some_pokemon.get_related('trainer')

        Need to get the Trainer class
        """
        cls = self.__class__

        foreign_key = cls.get_column_by_name(column_name)
        references = foreign_key.references

        return references.objects().where(
            references.get_column_by_name('id') == getattr(self, column_name)
        ).first()

    def __setitem__(self, key: str, value: t.Any):
        setattr(self, key, value)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __str__(self):
        row = ",".join([
            column.format_value(
                self[column.name]
            ) for column in self.Meta.columns
        ])
        return f'({row})'

    ###########################################################################

    @classmethod
    def get_column_by_name(cls, column_name: str):
        columns = [i for i in cls.Meta.columns if i.name == column_name]

        if len(columns) != 1:
            raise ValueError(
                f"Can't find a column called {column_name}."
            )

        return columns[0]

    @classmethod
    def ref(
        cls,
        column_name: str
    ) -> Column:
        """
        Used to get a copy of a column in a reference table.

        Example: trainer.name
        """
        local_column_name, reference_column_name = column_name.split('.')

        local_column = cls.get_column_by_name(local_column_name)

        if not isinstance(local_column, ForeignKey):
            raise ValueError(f"{local_column_name} isn't a ForeignKey")

        reference_column = local_column.references.get_column_by_name(
            reference_column_name
        )

        _reference_column = copy.deepcopy(reference_column)
        _reference_column.name = f'{local_column_name}.{reference_column_name}'
        return _reference_column

    ###########################################################################

    @classmethod
    def select(cls, *column_names: str) -> Select:
        """
        Needs to be a simple wrapper.

        One thing I *might* want to do is have an AS string, or just allow
        that in the string. For example, 'foo as bar'. I think I'll make
        it more explicit. So you do As('foo', 'bar'). So we can easily
        inspect that the column exists, and what we're trying to map it
        to doesn't already exist.
        """
        return Select(
            table=cls,
            column_names=column_names
        )

    @classmethod
    def insert(cls, *rows: 'Table') -> Insert:
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
        query = Insert(
            table=cls,
        )
        if rows:
            query.add(*rows)
        return query

    @classmethod
    def update(cls, **columns) -> Update:
        """
        await Pokemon.update(name='raichu').where(
            Pokemon.name='pikachu'
        ).run()
        """
        columns_str = ', '.join([
            f'{column} = {getattr(cls, column).format_value(value)}' for (
                column, value) in columns.items()
        ])

        return Update(
            table=cls,
            base=f'UPDATE {cls.Meta.tablename} SET {columns_str}'
        )

    @classmethod
    def delete(cls) -> Delete:
        """
        await Pokemon.delete().where(Pokemon.name='weedle').run()

        DELETE FROM pokemon where name = 'weedle'
        """
        return Delete(
            table=cls
        )

    @classmethod
    def create(cls) -> Create:
        """
        Create table, along with all columns.

        await Pokemon.create().run()
        """
        return Create(
            table=cls,
        )

    @classmethod
    def create_without_columns(cls) -> Raw:
        """
        Create the table, but with no columns (useful for migrations).

        await Pokemon.create().run()
        """
        return Raw(
            table=cls,
            base=f'CREATE TABLE "{cls.Meta.tablename}"()'
        )

    @classmethod
    def drop(cls) -> Drop:
        """
        Drops the table.

        await Pokemon.drop().run()
        """
        return Drop(
            table=cls,
        )

    @classmethod
    def raw(cls, sql: str) -> Raw:
        """
        await Pokemon.raw('select * from foo')
        """
        return Raw(
            table=cls,
            base=sql
        )

    @classmethod
    def alter(cls) -> Alter:
        """
        await Pokemon.alter().rename(Pokemon.power, 'rating')
        """
        return Alter(
            table=cls,
        )

    @classmethod
    def objects(cls) -> Objects:
        return Objects(
            table=cls
        )

    @classmethod
    def exists(cls) -> Exists:
        """
        This is tricky ... use it to check if a row exists ... not if the
        table exists.
        """
        return Exists(
            table=cls,
        )

    @classmethod
    def table_exists(cls) -> TableExists:
        return TableExists(
            table=cls,
        )
