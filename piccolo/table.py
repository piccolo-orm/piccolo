from __future__ import annotations
import copy
import typing as t

from piccolo.engine import Engine
from piccolo.columns import Column, PrimaryKey, ForeignKey
from piccolo.query import (
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
from piccolo.querystring import QueryString, Unquoted
from piccolo.utils import _camel_to_snake


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

        # In case super classes also have columns.
        if bases:
            for base in bases:
                if hasattr(base, 'Meta'):
                    _columns = getattr(base.Meta, 'columns', None)
                    if _columns:
                        # Don't copy over the primary key.
                        columns = [i for i in _columns if not
                                   isinstance(i, PrimaryKey)] + columns

        primary_key = PrimaryKey()
        namespace['id'] = primary_key
        table.id = primary_key

        for key, value in namespace.items():
            if issubclass(type(value), Column):
                columns.append(value)
                value._name = key
                value._table = table

        table.Meta.columns = columns
        table.Meta.non_default_columns = [
            i for i in columns if type(i) != PrimaryKey
        ]
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

    @property
    def update(cls) -> Update:
        """
        Update rows.

        await Band.update.values(
            {Band.name: "Spamalot"}
        ).where(Band.name=="Pythonistas")
        """
        return Update(
            table=cls,
        )


class Table(metaclass=TableMeta):

    class Meta:
        tablename = None
        columns: t.List[Column] = []
        non_default_columns: t.List[Column] = []
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

    @property
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
                i: getattr(self, i._name, None) for i in cls.Meta.columns
            }
            _id = kwargs.pop('id')
            return cls.update.values(kwargs).where(
                cls.id == _id
            )
        else:
            return cls.insert().add(self)

    @property
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
        ).first

    def __setitem__(self, key: str, value: t.Any):
        setattr(self, key, value)

    def __getitem__(self, key: str):
        return getattr(self, key)

    ###########################################################################

    @property
    def querystring(self) -> QueryString:
        """
        Used when inserting rows.
        """
        args_dict = {
            col._name: self[col._name] for col in self.Meta.columns
        }

        is_unquoted = (lambda arg: type(arg) == Unquoted)

        # Strip out any args which are unquoted.
        # TODO Not the cleanest place to have it (would rather have it handled
        # in the Querystring bundle logic) - might need refactoring.
        filtered_args = [
            i for i in args_dict.values() if not is_unquoted(i)
        ]

        # If unquoted, dump it straight into the query.
        query = ",".join([
            args_dict[column._name].value if is_unquoted(
                args_dict[column._name]
            ) else '{}' for column in self.Meta.columns
        ])
        return QueryString(
            f'({query})',
            *filtered_args
        )

    def __str__(self) -> str:
        return self.querystring.__str__()

    ###########################################################################

    @classmethod
    def get_column_by_name(cls, column_name: str) -> Column:
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
    # TODO - needs refactoring into Band.insert.rows(some_table_instance)
    def insert(cls, *rows: 'Table') -> Insert:
        """
        await Band.insert(
            Band(name="Pythonistas", popularity=500, manager=1)
        ).run()
        """
        query = Insert(
            table=cls,
        )
        if rows:
            query.add(*rows)
        return query

    @classmethod
    def raw(cls, sql: str) -> Raw:
        """
        await Band.raw('select * from foo')
        """
        return Raw(
            table=cls,
            base=QueryString(sql)
        )
