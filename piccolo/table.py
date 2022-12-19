from __future__ import annotations

import inspect
import itertools
import types
import typing as t
from dataclasses import dataclass, field

from piccolo.columns import Column
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    Array,
    Email,
    ForeignKey,
    Secret,
    Serial,
)
from piccolo.columns.defaults.base import Default
from piccolo.columns.indexes import IndexMethod
from piccolo.columns.m2m import (
    M2M,
    M2MAddRelated,
    M2MGetRelated,
    M2MRemoveRelated,
)
from piccolo.columns.readable import Readable
from piccolo.columns.reference import LAZY_COLUMN_REFERENCES
from piccolo.engine import Engine, engine_finder
from piccolo.query import (
    Alter,
    Count,
    Create,
    Delete,
    DropIndex,
    Exists,
    Insert,
    Objects,
    Raw,
    Select,
    TableExists,
    Update,
)
from piccolo.query.methods.create_index import CreateIndex
from piccolo.query.methods.indexes import Indexes
from piccolo.query.methods.refresh import Refresh
from piccolo.querystring import QueryString, Unquoted
from piccolo.utils import _camel_to_snake
from piccolo.utils.graphlib import TopologicalSorter
from piccolo.utils.sql_values import convert_to_sql_value
from piccolo.utils.sync import run_sync
from piccolo.utils.warnings import colored_warning

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Selectable

PROTECTED_TABLENAMES = ("user",)


TABLE_REGISTRY: t.List[t.Type[Table]] = []


@dataclass
class TableMeta:
    """
    This is used to store info about the table.
    """

    tablename: str = ""
    columns: t.List[Column] = field(default_factory=list)
    default_columns: t.List[Column] = field(default_factory=list)
    non_default_columns: t.List[Column] = field(default_factory=list)
    email_columns: t.List[Email] = field(default_factory=list)
    foreign_key_columns: t.List[ForeignKey] = field(default_factory=list)
    primary_key: Column = field(default_factory=Column)
    json_columns: t.List[t.Union[JSON, JSONB]] = field(default_factory=list)
    secret_columns: t.List[Secret] = field(default_factory=list)
    auto_update_columns: t.List[Column] = field(default_factory=list)
    tags: t.List[str] = field(default_factory=list)
    help_text: t.Optional[str] = None
    _db: t.Optional[Engine] = None
    m2m_relationships: t.List[M2M] = field(default_factory=list)

    # Records reverse foreign key relationships - i.e. when the current table
    # is the target of a foreign key. Used by external libraries such as
    # Piccolo API.
    _foreign_key_references: t.List[ForeignKey] = field(default_factory=list)

    @property
    def foreign_key_references(self) -> t.List[ForeignKey]:
        foreign_keys: t.List[ForeignKey] = list(self._foreign_key_references)
        lazy_column_references = LAZY_COLUMN_REFERENCES.for_tablename(
            tablename=self.tablename
        )
        foreign_keys.extend(lazy_column_references)

        return foreign_keys

    @property
    def db(self) -> Engine:
        if not self._db:
            db = engine_finder()
            if not db:
                raise Exception("Unable to find the engine")
            self._db = db

        return self._db

    @db.setter
    def db(self, value: Engine):
        self._db = value

    def refresh_db(self):
        self.db = engine_finder()

    def get_column_by_name(self, name: str) -> Column:
        """
        Returns a column which matches the given name. It will try and follow
        foreign keys too, for example if the name is 'foo.bar', where foo is
        a foreign key, and bar is a column on the referenced table.
        """
        components = name.split(".")
        column_name = components[0]
        column = [i for i in self.columns if i._meta.name == column_name]
        if len(column) != 1:
            raise ValueError(f"No matching column found with name == {name}")
        column_object = column[0]

        if len(components) > 1:
            for reference_name in components[1:]:
                try:
                    column_object = getattr(column_object, reference_name)
                except AttributeError as e:
                    raise ValueError(
                        f"Unable to find column - {reference_name}"
                    ) from e

        return column_object

    def get_auto_update_values(self) -> t.Dict[Column, t.Any]:
        """
        If columns have ``auto_update`` defined, then we retrieve these values.
        """
        output: t.Dict[Column, t.Any] = {}
        for column in self.auto_update_columns:
            value = column._meta.auto_update
            if callable(value):
                value = value()
            output[column] = value
        return output


class TableMetaclass(type):
    def __str__(cls):
        return cls._table_str()

    def __repr__(cls):
        """
        We override this, because by default Python will output something
        like::

            >>> repr(MyTable)
            <class 'my_app.tables.MyTable'>

        It's a very common pattern in Piccolo and its sister libraries to
        have ``Table`` class types as default values::

            # `SessionsBase` is a `Table` subclass:
            def session_auth(
                session_table: t.Type[SessionsBase] = SessionsBase
            ):
                ...

        This looks terrible in Sphinx's autodoc output, as Python's default
        repr contains angled brackets, which breaks the HTML output. So we just
        output the name instead. The user can still easily find which module a
        ``Table`` subclass belongs to by using ``MyTable.__module__``.

        """
        return cls.__name__


class Table(metaclass=TableMetaclass):
    """
    The class represents a database table. An instance represents a row.
    """

    # These are just placeholder values, so type inference isn't confused - the
    # actual values are set in __init_subclass__.
    _meta = TableMeta()

    def __init_subclass__(
        cls,
        tablename: t.Optional[str] = None,
        db: t.Optional[Engine] = None,
        tags: t.List[str] = None,
        help_text: t.Optional[str] = None,
    ):  # sourcery no-metrics
        """
        Automatically populate the _meta, which includes the tablename, and
        columns.

        :param tablename:
            Specify a custom tablename. By default the classname is converted
            to snakecase.
        :param db:
            Manually specify an engine to use for connecting to the database.
            Useful when writing simple scripts. If not set, the engine is
            imported from piccolo_conf.py using ``engine_finder``.
        :param tags:
            Used for filtering, for example by ``table_finder``.
        :param help_text:
            A user friendly description of what the table is used for. It isn't
            used in the database, but will be used by tools such a Piccolo
            Admin for tooltips.

        """
        if tags is None:
            tags = []
        tablename = tablename or _camel_to_snake(cls.__name__)

        if tablename in PROTECTED_TABLENAMES:
            raise ValueError(
                f"{tablename} is a protected name, please give your table a "
                "different name."
            )

        columns: t.List[Column] = []
        default_columns: t.List[Column] = []
        non_default_columns: t.List[Column] = []
        foreign_key_columns: t.List[ForeignKey] = []
        secret_columns: t.List[Secret] = []
        json_columns: t.List[t.Union[JSON, JSONB]] = []
        email_columns: t.List[Email] = []
        auto_update_columns: t.List[Column] = []
        primary_key: t.Optional[Column] = None
        m2m_relationships: t.List[M2M] = []

        attribute_names = itertools.chain(
            *[i.__dict__.keys() for i in reversed(cls.__mro__)]
        )
        unique_attribute_names = list(dict.fromkeys(attribute_names))

        for attribute_name in unique_attribute_names:
            if attribute_name.startswith("_"):
                continue

            attribute = getattr(cls, attribute_name)
            if isinstance(attribute, Column):
                # We have to copy, then override the existing column
                # definition, in case this column is inheritted from a mixin.
                # Otherwise, when we set attributes on that column, it will
                # effect all other users of that mixin.
                column = attribute.copy()
                setattr(cls, attribute_name, column)

                if column._meta.primary_key:
                    primary_key = column

                non_default_columns.append(column)
                columns.append(column)

                column._meta._name = attribute_name
                column._meta._table = cls

                if isinstance(column, Array):
                    column.base_column._meta._table = cls

                if isinstance(column, Email):
                    email_columns.append(column)

                if isinstance(column, Secret):
                    secret_columns.append(column)

                if isinstance(column, ForeignKey):
                    foreign_key_columns.append(column)

                if isinstance(column, (JSON, JSONB)):
                    json_columns.append(column)

                if column._meta.auto_update is not ...:
                    auto_update_columns.append(column)

            if isinstance(attribute, M2M):
                attribute._meta._name = attribute_name
                attribute._meta._table = cls
                m2m_relationships.append(attribute)

        if not primary_key:
            primary_key = cls._create_serial_primary_key()
            setattr(cls, "id", primary_key)

            columns.insert(0, primary_key)  # PK should be added first
            default_columns.append(primary_key)

        cls._meta = TableMeta(
            tablename=tablename,
            columns=columns,
            default_columns=default_columns,
            non_default_columns=non_default_columns,
            email_columns=email_columns,
            primary_key=primary_key,
            foreign_key_columns=foreign_key_columns,
            json_columns=json_columns,
            secret_columns=secret_columns,
            auto_update_columns=auto_update_columns,
            tags=tags,
            help_text=help_text,
            _db=db,
            m2m_relationships=m2m_relationships,
        )

        for foreign_key_column in foreign_key_columns:
            # ForeignKey columns require additional setup based on their
            # parent Table.
            foreign_key_setup_response = foreign_key_column._setup(
                table_class=cls
            )
            if foreign_key_setup_response.is_lazy:
                LAZY_COLUMN_REFERENCES.foreign_key_columns.append(
                    foreign_key_column
                )

        TABLE_REGISTRY.append(cls)

    def __init__(
        self,
        _data: t.Dict[Column, t.Any] = None,
        _ignore_missing: bool = False,
        _exists_in_db: bool = False,
        **kwargs,
    ):
        """
        The constructor can be used to assign column values.

        .. note::
            The ``_data``, ``_ignore_missing``, and ``_exists_in_db``
            arguments are prefixed with an underscore to help prevent a clash
            with a column name which might be passed in via kwargs.

        :param _data:
            There's two ways of passing in the data for each column. Firstly,
            you can use kwargs::

                Band(name="Pythonistas")

            Secondly, you can pass in a dictionary which maps column classes to
            values::

                Band({Band.name: 'Pythonistas'})

            The advantage of this second approach is it's more strongly typed,
            and linters such as flake8 or MyPy will more easily detect typos.

        :param _ignore_missing:
            If ``False`` a ``ValueError`` will be raised if any column values
            haven't been provided.
        :param _exists_in_db:
            Used internally to track whether this row exists in the database.

        """
        _data = _data or {}

        self._exists_in_db = _exists_in_db

        for column in self._meta.columns:
            value = _data.get(column, ...)

            if kwargs:
                if value is ...:
                    value = kwargs.pop(column._meta.name, ...)

                if value is ...:
                    value = kwargs.pop(
                        t.cast(str, column._meta.db_column_name), ...
                    )

            if value is ...:
                value = column.get_default_value()

                if isinstance(value, Default):
                    value = value.python()

                if (
                    (value is None)
                    and (not column._meta.null)
                    and not _ignore_missing
                ):
                    raise ValueError(f"{column._meta.name} wasn't provided")

            self[column._meta.name] = value

        unrecognized = kwargs.keys()
        if unrecognized:
            unrecognised_list = list(unrecognized)
            raise ValueError(f"Unrecognized columns - {unrecognised_list}")

    @classmethod
    def _create_serial_primary_key(cls) -> Serial:
        pk = Serial(index=False, primary_key=True, db_column_name="id")
        pk._meta._name = "id"
        pk._meta._table = cls

        return pk

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> Table:
        """
        Used when loading fixtures. It can be overriden by subclasses in case
        they have specific logic / validation which needs running when loading
        fixtures.
        """
        return cls(**data)

    ###########################################################################

    def save(
        self, columns: t.Optional[t.Sequence[t.Union[Column, str]]] = None
    ) -> t.Union[Insert, Update]:
        """
        A proxy to an insert or update query.

        :param columns:
            Only the specified columns will be synced back to the database
            when doing an update. For example:

            .. code-block:: python

                band = await Band.objects().first()
                band.popularity = 2000
                await band.save(columns=[Band.popularity])

            If ``columns=None`` (the default) then all columns will be synced
            back to the database.

        """
        cls = self.__class__

        # New row - insert
        if not self._exists_in_db:
            return cls.insert(self).returning(cls._meta.primary_key)

        # Pre-existing row - update
        if columns is None:
            column_instances = [
                i for i in cls._meta.columns if not i._meta.primary_key
            ]
        else:
            column_instances = [
                self._meta.get_column_by_name(i) if isinstance(i, str) else i
                for i in columns
            ]

        values: t.Dict[Column, t.Any] = {
            i: getattr(self, i._meta.name, None) for i in column_instances
        }

        # Assign any `auto_update` values
        if cls._meta.auto_update_columns:
            auto_update_values = cls._meta.get_auto_update_values()
            values.update(auto_update_values)
            for column, value in auto_update_values.items():
                setattr(self, column._meta.name, value)

        return cls.update(
            values,  # type: ignore
            # We've already included the `auto_update` columns, so no need
            # to do it again:
            use_auto_update=False,
        ).where(
            cls._meta.primary_key
            == getattr(self, self._meta.primary_key._meta.name)
        )

    def remove(self) -> Delete:
        """
        A proxy to a delete query.
        """
        primary_key_value = getattr(self, self._meta.primary_key._meta.name)

        if not primary_key_value:
            raise ValueError("Can only delete pre-existing rows with a PK.")

        setattr(self, self._meta.primary_key._meta.name, None)

        return self.__class__.delete().where(
            self.__class__._meta.primary_key == primary_key_value
        )

    def refresh(
        self, columns: t.Optional[t.Sequence[Column]] = None
    ) -> Refresh:
        """
        Used to fetch the latest data for this instance from the database.
        Modifies the instance in place, but also returns it as a convenience.

        :param columns:
            If you only want to refresh certain columns, specify them here.
            Otherwise all columns are refreshed.

        Example usage::

            # Get an instance from the database.
            instance = await Band.objects.first()

            # Later on we can refresh this instance with the latest data
            # from the database, in case it has gotten stale.
            await instance.refresh()

            # Alternatively, running it synchronously:
            instance.refresh().run_sync()

        """
        return Refresh(instance=self, columns=columns)

    def get_related(self, foreign_key: t.Union[ForeignKey, str]) -> Objects:
        """
        Used to fetch a ``Table`` instance, for the target of a foreign key.

        .. code-block:: python

            band = await Band.objects().first()
            manager = await band.get_related(Band.manager)
            >>> print(manager.name)
            'Guido'

        It can only follow foreign keys one level currently.
        i.e. ``Band.manager``, but not ``Band.manager.x.y.z``.

        """
        if isinstance(foreign_key, str):
            column = self._meta.get_column_by_name(foreign_key)
            if isinstance(column, ForeignKey):
                foreign_key = column

        if not isinstance(foreign_key, ForeignKey):
            raise ValueError(
                "foreign_key isn't a ForeignKey instance,  or the name of a "
                "ForeignKey column."
            )

        column_name = foreign_key._meta.name

        references: t.Type[
            Table
        ] = foreign_key._foreign_key_meta.resolved_references

        return (
            references.objects()
            .where(
                references._meta.get_column_by_name(
                    self._meta.primary_key._meta.name
                )
                == getattr(self, column_name)
            )
            .first()
        )

    def get_m2m(self, m2m: M2M) -> M2MGetRelated:
        """
        Get all matching rows via the join table.

        .. code-block:: python

            >>> band = await Band.objects().get(Band.name == "Pythonistas")
            >>> await band.get_m2m(Band.genres)
            [<Genre: 1>, <Genre: 2>]

        """
        return M2MGetRelated(row=self, m2m=m2m)

    def add_m2m(
        self,
        *rows: Table,
        m2m: M2M,
        extra_column_values: t.Dict[t.Union[Column, str], t.Any] = {},
    ) -> M2MAddRelated:
        """
        Save the row if it doesn't already exist in the database, and insert
        an entry into the joining table.

        .. code-block:: python

            >>> band = await Band.objects().get(Band.name == "Pythonistas")
            >>> await band.add_m2m(
            ...     Genre(name="Punk rock"),
            ...     m2m=Band.genres
            ... )
            [{'id': 1}]

        :param extra_column_values:
            If the joining table has additional columns besides the two
            required foreign keys, you can specify the values for those
            additional columns. For example, if this is our joining table:

            .. code-block:: python

                class GenreToBand(Table):
                    band = ForeignKey(Band)
                    genre = ForeignKey(Genre)
                    reason = Text()

            We can provide the ``reason`` value:

            .. code-block:: python

                await band.add_m2m(
                    Genre(name="Punk rock"),
                    m2m=Band.genres,
                    extra_column_values={
                        "reason": "Their second album was very punk."
                    }
                )

        """
        return M2MAddRelated(
            target_row=self,
            rows=rows,
            m2m=m2m,
            extra_column_values=extra_column_values,
        )

    def remove_m2m(self, *rows: Table, m2m: M2M) -> M2MRemoveRelated:
        """
        Remove the rows from the joining table.

        .. code-block:: python

            >>> band = await Band.objects().get(Band.name == "Pythonistas")
            >>> genre = await Genre.objects().get(Genre.name == "Rock")
            >>> await band.remove_m2m(
            ...     genre,
            ...     m2m=Band.genres
            ... )

        """
        return M2MRemoveRelated(
            target_row=self,
            rows=rows,
            m2m=m2m,
        )

    def to_dict(self, *columns: Column) -> t.Dict[str, t.Any]:
        """
        A convenience method which returns a dictionary, mapping column names
        to values for this table instance.

        .. code-block:: python

            instance = await Manager.objects().get(
                Manager.name == 'Guido'
            )

            >>> instance.to_dict()
            {'id': 1, 'name': 'Guido'}

        If the columns argument is provided, only those columns are included in
        the output. It also works with column aliases.

        .. code-block:: python

            >>> instance.to_dict(Manager.id, Manager.name.as_alias('title'))
            {'id': 1, 'title': 'Guido'}

        """
        # Make sure we're only looking at columns for the current table. If
        # someone passes in a column for a sub table (for example
        # `Band.manager.name`), we need to add `Band.manager` so the nested
        # value appears in the output.
        filtered_columns = []
        for column in columns:
            if column._meta.table == self.__class__:
                filtered_columns.append(column)
            else:
                for parent_column in column._meta.call_chain:
                    if parent_column._meta.table == self.__class__:
                        filtered_columns.append(parent_column)
                        break

        alias_names = {
            column._meta.name: column._alias for column in filtered_columns
        }

        output = {}
        for column in filtered_columns if columns else self._meta.columns:
            value = getattr(self, column._meta.name)
            if isinstance(value, Table):
                value = value.to_dict(*columns)

            output[
                alias_names.get(column._meta.name) or column._meta.name
            ] = value
        return output

    def __setitem__(self, key: str, value: t.Any):
        setattr(self, key, value)

    def __getitem__(self, key: str):
        return getattr(self, key)

    ###########################################################################

    @classmethod
    def _get_related_readable(cls, column: ForeignKey) -> Readable:
        """
        Used for getting a readable from a foreign key.
        """
        readable: Readable = (
            column._foreign_key_meta.resolved_references.get_readable()
        )

        output_columns = []

        for readable_column in readable.columns:
            output_column = column
            for fk in readable_column._meta.call_chain:
                output_column = getattr(output_column, fk._meta.name)
            output_column = getattr(output_column, readable_column._meta.name)
            output_columns.append(output_column)

        output_name = f"{column._meta.name}_readable"

        return Readable(
            template=readable.template,
            columns=output_columns,
            output_name=output_name,
        )

    @classmethod
    def get_readable(cls) -> Readable:
        """
        Creates a readable representation of the row.
        """
        return Readable(template="%s", columns=[cls._meta.primary_key])

    ###########################################################################

    @property
    def querystring(self) -> QueryString:
        """
        Used when inserting rows.
        """
        args_dict = {}
        for col in self._meta.columns:
            column_name = col._meta.name
            value = convert_to_sql_value(value=self[column_name], column=col)
            args_dict[column_name] = value

        def is_unquoted(arg):
            return type(arg) == Unquoted

        # Strip out any args which are unquoted.
        filtered_args = [i for i in args_dict.values() if not is_unquoted(i)]

        # If unquoted, dump it straight into the query.
        query = ",".join(
            [
                args_dict[column._meta.name].value
                if is_unquoted(args_dict[column._meta.name])
                else "{}"
                for column in self._meta.columns
            ]
        )
        return QueryString(f"({query})", *filtered_args)

    def __str__(self) -> str:
        return self.querystring.__str__()

    def __repr__(self) -> str:
        pk = (
            None
            if not self._exists_in_db
            else getattr(self, self._meta.primary_key._meta.name, None)
        )
        return f"<{self.__class__.__name__}: {pk}>"

    ###########################################################################
    # Classmethods

    @classmethod
    def all_related(
        cls, exclude: t.List[t.Union[str, ForeignKey]] = None
    ) -> t.List[Column]:
        """
        Used in conjunction with ``objects`` queries. Just as we can use
        ``all_related`` on a ``ForeignKey``, you can also use it for the table
        at the root of the query, which will return each related row as a
        nested object. For example:

        .. code-block:: python

            concert = await Concert.objects(
                Concert.all_related()
            )

            >>> concert.band_1
            <Band: 1>
            >>> concert.band_2
            <Band: 2>
            >>> concert.venue
            <Venue: 1>

        This is mostly useful when the table has a lot of foreign keys, and
        typing them out by hand would be tedious. It's equivalent to:

        .. code-block:: python

            concert = await Concert.objects(
                Concert.venue,
                Concert.band_1,
                Concert.band_2
            )

        :param exclude:
            You can request all columns, except these.

        """
        if exclude is None:
            exclude = []
        excluded_column_names = [
            i._meta.name if isinstance(i, ForeignKey) else i for i in exclude
        ]

        return [
            i
            for i in cls._meta.foreign_key_columns
            if i._meta.name not in excluded_column_names
        ]

    @classmethod
    def all_columns(
        cls, exclude: t.Sequence[t.Union[str, Column]] = None
    ) -> t.List[Column]:
        """
        Used in conjunction with ``select`` queries. Just as we can use
        ``all_columns`` to retrieve all of the columns from a related table,
        we can also use it at the root of our query to get all of the columns
        for the root table. For example:

        .. code-block:: python

            await Band.select(
                Band.all_columns(),
                Band.manager.all_columns()
            )

        This is mostly useful when the table has a lot of columns, and typing
        them out by hand would be tedious.

        :param exclude:
            You can request all columns, except these.

        """
        if exclude is None:
            exclude = []
        excluded_column_names = [
            i._meta.name if isinstance(i, Column) else i for i in exclude
        ]

        return [
            i
            for i in cls._meta.columns
            if i._meta.name not in excluded_column_names
        ]

    @classmethod
    def ref(cls, column_name: str) -> Column:
        """
        Used to get a copy of a column from a table referenced by a
        ``ForeignKey`` column. It's unlikely an end user of this library will
        ever need to do this, but other libraries built on top of Piccolo may
        need this functionality.

        .. code-block:: python

            Band.ref('manager.name')

        """
        local_column_name, reference_column_name = column_name.split(".")

        local_column = cls._meta.get_column_by_name(local_column_name)

        if not isinstance(local_column, ForeignKey):
            raise ValueError(f"{local_column_name} isn't a ForeignKey")

        referenced_table = local_column._foreign_key_meta.resolved_references
        reference_column = referenced_table._meta.get_column_by_name(
            reference_column_name
        )

        _reference_column = reference_column.copy()
        _reference_column._meta.name = (
            f"{local_column_name}.{reference_column_name}"
        )
        return _reference_column

    @classmethod
    def insert(cls, *rows: "Table") -> Insert:
        """
        Insert rows into the database.

        .. code-block:: python

            await Band.insert(
                Band(name="Pythonistas", popularity=500, manager=1)
            )

        """
        query = Insert(table=cls).returning(cls._meta.primary_key)
        if rows:
            query.add(*rows)
        return query

    @classmethod
    def raw(cls, sql: str, *args: t.Any) -> Raw:
        """
        Execute raw SQL queries on the underlying engine - use with caution!

        .. code-block:: python

            await Band.raw('select * from band')

        Or passing in parameters:

        .. code-block:: python

            await Band.raw("select * from band where name = {}", 'Pythonistas')

        """
        return Raw(table=cls, querystring=QueryString(sql, *args))

    @classmethod
    def _process_column_args(
        cls, *columns: t.Union[Selectable, str]
    ) -> t.Sequence[Selectable]:
        """
        Users can specify some column arguments as either Column instances, or
        as strings representing the column name, for convenience.
        Convert any string arguments to column instances.
        """
        return [
            cls._meta.get_column_by_name(column)
            if (isinstance(column, str))
            else column
            for column in columns
        ]

    @classmethod
    def select(
        cls, *columns: t.Union[Selectable, str], exclude_secrets=False
    ) -> Select:
        """
        Get data in the form of a list of dictionaries, with each dictionary
        representing a row.

        These are all equivalent:

        .. code-block:: python

            await Band.select().columns(Band.name)
            await Band.select(Band.name)
            await Band.select('name')

        :param exclude_secrets:
            If ``True``, any columns with ``secret=True`` are omitted from the
            response. For example, we use this for the password column of
            :class:`BaseUser <piccolo.apps.user.tables.BaseUser>`. Even though
            the passwords are hashed, you still don't want them being passed
            over the network if avoidable.

        """
        _columns = cls._process_column_args(*columns)
        return Select(
            table=cls, columns_list=_columns, exclude_secrets=exclude_secrets
        )

    @classmethod
    def delete(cls, force=False) -> Delete:
        """
        Delete rows from the table.

        .. code-block:: python

            await Band.delete().where(Band.name == 'Pythonistas')

        :param force:
            Unless set to ``True``, deletions aren't allowed without a
            ``where`` clause, to prevent accidental mass deletions.

        """
        return Delete(table=cls, force=force)

    @classmethod
    def create_table(
        cls, if_not_exists=False, only_default_columns=False
    ) -> Create:
        """
        Create table, along with all columns.

        .. code-block:: python

            await Band.create_table()

        """
        return Create(
            table=cls,
            if_not_exists=if_not_exists,
            only_default_columns=only_default_columns,
        )

    @classmethod
    def alter(cls) -> Alter:
        """
        Used to modify existing tables and columns.

        .. code-block:: python

            await Band.alter().rename_column(Band.popularity, 'rating')

        """
        return Alter(table=cls)

    @classmethod
    def objects(
        cls, *prefetch: t.Union[ForeignKey, t.List[ForeignKey]]
    ) -> Objects:
        """
        Returns a list of table instances (each representing a row), which you
        can modify and then call 'save' on, or can delete by calling 'remove'.

        .. code-block:: python

            pythonistas = await Band.objects().where(
                Band.name == 'Pythonistas'
            ).first()

            pythonistas.name = 'Pythonistas Reborn'

            await pythonistas.save()

            # Or to remove it from the database:
            await pythonistas.remove()

        :param prefetch:
            Rather than returning the primary key value of this related table,
            a nested object will be returned for the row on the related table.

            .. code-block:: python

                # Without nested
                band = await Band.objects().first()
                >>> band.manager
                1

                # With nested
                band = await Band.objects(Band.manager).first()
                >>> band.manager
                <Band 1>

        """
        return Objects(table=cls, prefetch=prefetch)

    @classmethod
    def count(cls) -> Count:
        """
        Count the number of matching rows.

        .. code-block:: python

            await Band.count().where(Band.popularity > 1000)

        """
        return Count(table=cls)

    @classmethod
    def exists(cls) -> Exists:
        """
        Use it to check if a row exists, not if the table exists.

        .. code-block:: python

            await Band.exists().where(Band.name == 'Pythonistas')

        """
        return Exists(table=cls)

    @classmethod
    def table_exists(cls) -> TableExists:
        """
        Check if the table exists in the database.

        .. code-block:: python

            await Band.table_exists()

        """
        return TableExists(table=cls)

    @classmethod
    def update(
        cls,
        values: t.Dict[t.Union[Column, str], t.Any] = None,
        force: bool = False,
        use_auto_update: bool = True,
        **kwargs,
    ) -> Update:
        """
        Update rows.

        All of the following work, though the first is preferable:

        .. code-block:: python

            await Band.update(
                {Band.name: "Spamalot"}
            ).where(
                Band.name == "Pythonistas"
            )

            await Band.update(
                {"name": "Spamalot"}
            ).where(
                Band.name == "Pythonistas"
            )

            await Band.update(
                name="Spamalot"
            ).where(
                Band.name == "Pythonistas"
            )

        :param force:
            Unless set to ``True``, updates aren't allowed without a
            ``where`` clause, to prevent accidental mass overriding of data.

        :param use_auto_update:
            Whether to use the ``auto_update`` values on any columns. See
            the ``auto_update`` argument on
            :class:`Column <piccolo.columns.base.Column>` for more information.

        """
        if values is None:
            values = {}
        values = dict(values, **kwargs)

        if use_auto_update and cls._meta.auto_update_columns:
            values.update(cls._meta.get_auto_update_values())  # type: ignore

        return Update(table=cls, force=force).values(values)

    @classmethod
    def indexes(cls) -> Indexes:
        """
        Returns a list of the indexes for this tables.

        .. code-block:: python

            await Band.indexes()

        """
        return Indexes(table=cls)

    @classmethod
    def create_index(
        cls,
        columns: t.List[t.Union[Column, str]],
        method: IndexMethod = IndexMethod.btree,
        if_not_exists: bool = False,
    ) -> CreateIndex:
        """
        Create a table index. If multiple columns are specified, this refers
        to a multicolumn index, rather than multiple single column indexes.

        .. code-block:: python

            await Band.create_index([Band.name])

        """
        return CreateIndex(
            table=cls,
            columns=columns,
            method=method,
            if_not_exists=if_not_exists,
        )

    @classmethod
    def drop_index(
        cls, columns: t.List[t.Union[Column, str]], if_exists: bool = True
    ) -> DropIndex:
        """
        Drop a table index. If multiple columns are specified, this refers
        to a multicolumn index, rather than multiple single column indexes.

        .. code-block:: python

            await Band.drop_index([Band.name])

        """
        return DropIndex(table=cls, columns=columns, if_exists=if_exists)

    ###########################################################################

    @classmethod
    def _get_index_name(cls, column_names: t.List[str]) -> str:
        """
        Generates an index name from the table name and column names.
        """
        return "_".join([cls._meta.tablename] + column_names)

    ###########################################################################

    @classmethod
    def _table_str(
        cls, abbreviated=False, excluded_params: t.List[str] = None
    ):
        """
        Returns a basic string representation of the table and its columns.
        Used by the playground.

        :param abbreviated:
            If True, a very high level representation is printed out.
        :param excluded_params:
            Lets us find a middle ground between outputting every kwarg, and
            the abbreviated version with very few kwargs. For example
            `['index_method']`, if we want to show all kwargs but index_method.

        """
        if excluded_params is None:
            excluded_params = []
        spacer = "\n    "
        columns = []
        for col in cls._meta.columns:
            params: t.List[str] = []
            for key, value in col._meta.params.items():
                if key in excluded_params:
                    continue

                _value: str = ""
                if inspect.isclass(value):
                    _value = value.__name__
                    params.append(f"{key}={_value}")
                else:
                    _value = repr(value)
                    if not abbreviated:
                        params.append(f"{key}={_value}")
            params_string = ", ".join(params)
            columns.append(
                f"{col._meta.name} = {col.__class__.__name__}({params_string})"
            )
        columns_string = spacer.join(columns)
        tablename = repr(cls._meta.tablename)

        parent_class_name = cls.mro()[1].__name__

        class_args = (
            parent_class_name
            if abbreviated
            else f"{parent_class_name}, tablename={tablename}"
        )

        return (
            f"class {cls.__name__}({class_args}):\n" f"    {columns_string}\n"
        )


def create_table_class(
    class_name: str,
    bases: t.Tuple[t.Type] = (Table,),
    class_kwargs: t.Dict[str, t.Any] = {},
    class_members: t.Dict[str, t.Any] = {},
) -> t.Type[Table]:
    """
    Used to dynamically create ``Table``subclasses at runtime. Most users
    will not require this. It's mostly used internally for Piccolo's
    migrations.

    :param class_name:
        For example `'MyTable'`.
    :param bases:
        A tuple of parent classes - usually just `(Table,)`.
    :param class_kwargs:
        For example, `{'tablename': 'my_custom_tablename'}`.
    :param class_members:
        For example, `{'my_column': Varchar()}`.

    """
    return t.cast(
        t.Type[Table],
        types.new_class(
            name=class_name,
            bases=bases,
            kwds=class_kwargs,
            exec_body=lambda namespace: namespace.update(class_members),
        ),
    )


###############################################################################
# Quickly create or drop database tables from Piccolo `Table` classes.


async def create_db_tables(
    *tables: t.Type[Table], if_not_exists: bool = False
) -> None:
    """
    Creates the database table for each ``Table`` class passed in. The tables
    are created in the correct order, based on their foreign keys.

    :param tables:
        The tables to create in the database.
    :param if_not_exists:
        No errors will be raised if any of the tables already exist in the
        database.

    """
    if tables:
        engine = tables[0]._meta.db
    else:
        return

    sorted_table_classes = sort_table_classes(list(tables))

    atomic = engine.atomic()
    atomic.add(
        *[
            table.create_table(if_not_exists=if_not_exists)
            for table in sorted_table_classes
        ]
    )
    await atomic.run()


def create_db_tables_sync(
    *tables: t.Type[Table], if_not_exists: bool = False
) -> None:
    """
    A sync wrapper around :func:`create_db_tables`.
    """
    run_sync(create_db_tables(*tables, if_not_exists=if_not_exists))


def create_tables(*tables: t.Type[Table], if_not_exists: bool = False) -> None:
    """
    This original implementation has been replaced, because it was synchronous,
    and felt at odds with the rest of the Piccolo codebase which is async
    first.

    Instead, use create_db_tables for asynchronous code, or
    create_db_tables_sync for synchronous code
    """
    colored_warning(
        "`create_tables` is deprecated and will be removed in v1 of Piccolo. "
        "Use `await create_db_tables(...)` or `create_db_tables_sync(...)` "
        "instead.",
        category=DeprecationWarning,
    )

    return create_db_tables_sync(*tables, if_not_exists=if_not_exists)


async def drop_db_tables(*tables: t.Type[Table]) -> None:
    """
    Drops the database table for each ``Table`` class passed in. The tables
    are dropped in the correct order, based on their foreign keys.

    :param tables:
        The tables to delete from the database.

    """
    if tables:
        engine = tables[0]._meta.db
    else:
        return

    if engine.engine_type == "sqlite":
        # SQLite doesn't support CASCADE, so we have to drop them in the
        # correct order.
        sorted_table_classes = reversed(sort_table_classes(list(tables)))
        atomic = engine.atomic()
        atomic.add(
            *[
                Alter(table=table).drop_table(if_exists=True)
                for table in sorted_table_classes
            ]
        )
    else:
        atomic = engine.atomic()
        atomic.add(
            *[
                table.alter().drop_table(cascade=True, if_exists=True)
                for table in tables
            ]
        )

    await atomic.run()


def drop_db_tables_sync(*tables: t.Type[Table]) -> None:
    """
    A sync wrapper around :func:`drop_db_tables`.
    """
    run_sync(drop_db_tables(*tables))


def drop_tables(*tables: t.Type[Table]) -> None:
    """
    This original implementation has been replaced, because it was synchronous,
    and felt at odds with the rest of the Piccolo codebase which is async
    first.

    Instead, use drop_db_tables for asynchronous code, or
    drop_db_tables_sync for synchronous code
    """
    colored_warning(
        "`drop_tables` is deprecated and will be removed in v1 of Piccolo. "
        "Use `await drop_db_tables(...)` or `drop_db_tables_sync(...)` "
        "instead.",
        category=DeprecationWarning,
    )

    return drop_db_tables_sync(*tables)


###############################################################################


def sort_table_classes(
    table_classes: t.List[t.Type[Table]],
) -> t.List[t.Type[Table]]:
    """
    Sort the table classes based on their foreign keys, so they can be created
    in the correct order.
    """
    table_class_dict = {
        table_class._meta.tablename: table_class
        for table_class in table_classes
    }

    graph = _get_graph(table_classes)

    sorter = TopologicalSorter(graph)
    ordered_tablenames = tuple(sorter.static_order())

    output: t.List[t.Type[Table]] = []
    for tablename in ordered_tablenames:
        table_class = table_class_dict.get(tablename)
        if table_class is not None:
            output.append(table_class)

    return output


def _get_graph(
    table_classes: t.List[t.Type[Table]],
    iterations: int = 0,
    max_iterations: int = 5,
) -> t.Dict[str, t.Set[str]]:
    """
    Analyses the tables based on their foreign keys, and returns a data
    structure like:

    .. code-block:: python

        {'band': {'manager'}, 'concert': {'band', 'venue'}, 'manager': set()}

    The keys are tablenames, and the values are tablenames directly connected
    to it via a foreign key.

    """
    output: t.Dict[str, t.Set[str]] = {}

    if iterations >= max_iterations:
        return output

    for table_class in table_classes:
        dependents: t.Set[str] = set()
        for fk in table_class._meta.foreign_key_columns:
            referenced_table = fk._foreign_key_meta.resolved_references

            if referenced_table._meta.tablename == table_class._meta.tablename:
                # Most like a recursive link (using ForeignKey('self')).
                continue

            dependents.add(referenced_table._meta.tablename)

            # We also recursively check the related tables to get a fuller
            # picture of the schema and relationships.
            if referenced_table._meta.tablename not in output:
                output.update(
                    _get_graph(
                        [referenced_table],
                        iterations=iterations + 1,
                    )
                )

        output[table_class._meta.tablename] = dependents

    return output
