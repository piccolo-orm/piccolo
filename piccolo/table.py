import copy
import typing as t

from .engine import Engine
from .columns import Column, PrimaryKey, ForeignKey
from .query import (
    Alter,
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


class TableMeta(type):

    def __new__(cls, name, bases, namespace, **kwds):
        """
        Automatically populate the tablename, and columns.
        """
        table = super().__new__(cls, name, bases, namespace)

        Meta = namespace.get('Meta')
        if (not Meta) or (Meta in [i.Meta for i in bases]):
            # We're inheritting a Meta from a parent class - give this class
            # its own Meta
            Meta = type('Meta', tuple(), {})
            table.Meta = Meta

        tablename = getattr(Meta, 'tablename', None) if Meta else None
        if not tablename:
            table.Meta.tablename = _camel_to_snake(name)

        columns = []
        for key, value in namespace.items():
            if issubclass(type(value), Column):
                columns.append(value)
                value._name = key
                value._table = table

        # In case super classes also have columns.
        if bases:
            for base in bases:
                if hasattr(base, 'Meta'):
                    _columns = getattr(base.Meta, 'columns', None)
                    if _columns:
                        columns = _columns + columns

        table.Meta.columns = columns
        return table

    ###########################################################################

    def __str__(cls):
        """
        Returns a basic string representation of the table and its columns.

        Used by the playground.
        """
        spacer = '\n    '
        columns = []
        for col in cls.Meta.columns:
            if type(col) == ForeignKey:
                columns.append(
                    f'{col._name} = ForeignKey({col.references.__name__})'
                )
            else:
                columns.append(f'{col._name} = {col.__class__.__name__}()')
        columns_string = spacer.join(columns)
        return (
            f'class {cls.__name__}(Table):\n'
            f'    {columns_string}\n'
        )

    ###########################################################################
    # Class properties
    # TODO - might need to rework, tab completion only works in some versions
    # of iPython.

    @property
    def delete(cls) -> Delete:
        """
        await Band.delete.where(Band.name == 'CSharps').run()
        """
        return Delete(
            table=cls
        )

    @property
    def create(cls) -> Create:
        """
        Create table, along with all columns.

        await Band.create.run()
        """
        return Create(
            table=cls,
        )

    @property
    def create_without_columns(cls) -> Raw:
        """
        Create the table, but with no columns (useful for migrations).

        await Band.create.run()
        """
        return Raw(
            table=cls,
            base=f'CREATE TABLE "{cls.Meta.tablename}"()'
        )

    @property
    def drop(cls) -> Drop:
        """
        Drops the table.

        await Band.drop.run()
        """
        return Drop(
            table=cls,
        )

    @property
    def alter(cls) -> Alter:
        """
        await Band.alter.rename(Band.popularity, 'rating')
        """
        return Alter(
            table=cls,
        )

    @property
    def objects(cls) -> Objects:
        return Objects(
            table=cls
        )

    @property
    def exists(cls) -> Exists:
        """
        Use it to check if a row exists ... not if the table exists.
        """
        return Exists(
            table=cls,
        )

    @property
    def table_exists(cls) -> TableExists:
        return TableExists(
            table=cls,
        )

    @property
    def select(cls) -> Select:
        """
        Get data.

        await Band.select.columns(Band.name).run()
        """
        return Select(
            table=cls,
        )


class Table(metaclass=TableMeta):

    id = PrimaryKey()

    class Meta:
        tablename = None
        columns: t.List[Column] = []
        db: t.Optional[Engine] = None

    def __init__(self, **kwargs):
        """
        TODO:
        Need to know the memory size of each instance ... can't be
        massive.
        """
        for column in self.Meta.columns:
            value = kwargs.pop(column._name, None)
            if not value:
                if column.default:
                    # Can't use inspect - can't tell that datetime.datetime.now
                    # is a callable.
                    is_callable = hasattr(column.default, '__call__')
                    value = column.default() if is_callable else column.default
                else:
                    if not column.null:
                        raise ValueError(f"{column._name} wasn't provided")
            self[column._name] = value

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
                i._name: getattr(self, i._name, None) for i in cls.Meta.columns
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

        return self.__class__.delete.where(
            self.__class__.id == _id
        )

    def get_related(self, column_name: str):
        """
        some_band.get_related('manager')
        """
        cls = self.__class__

        foreign_key = cls.get_column_by_name(column_name)  # type: ignore
        references = foreign_key.references

        return references.objects.where(
            references.get_column_by_name('id') == getattr(self, column_name)
        ).first()

    def __setitem__(self, key: str, value: t.Any):
        setattr(self, key, value)

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __str__(self):
        row = ",".join([
            column.format_value(
                self[column._name]
            ) for column in self.Meta.columns
        ])
        return f'({row})'

    ###########################################################################

    @classmethod
    def get_column_by_name(cls, column_name: str):
        columns = [i for i in cls.Meta.columns if i._name == column_name]

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

        Example: manager.name
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
    def insert(cls, *rows: 'Table') -> Insert:
        """
        await Band.insert(
            Band(name="jigglypuff", popularity=500, manager="florence")
        ).run()
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
        await Band.update(name='Pythonistas').where(
            Band.name='Spamalot'
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
    def raw(cls, sql: str) -> Raw:
        """
        await Band.raw('select * from foo')
        """
        return Raw(
            table=cls,
            base=sql
        )
