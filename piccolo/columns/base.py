from __future__ import annotations

import copy
import datetime
import decimal
import inspect
import typing as t
import uuid
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field, fields
from enum import Enum

from piccolo.columns.choices import Choice
from piccolo.columns.combination import Where
from piccolo.columns.defaults.base import Default
from piccolo.columns.defaults.interval import IntervalCustom
from piccolo.columns.indexes import IndexMethod
from piccolo.columns.operators.comparison import (
    ComparisonOperator,
    Equal,
    GreaterEqualThan,
    GreaterThan,
    ILike,
    In,
    IsNotNull,
    IsNull,
    LessEqualThan,
    LessThan,
    Like,
    NotEqual,
    NotIn,
    NotLike,
)
from piccolo.columns.reference import LazyTableReference
from piccolo.utils.warnings import colored_warning

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.column_types import ForeignKey
    from piccolo.table import Table


class OnDelete(str, Enum):
    """
    Used by :class:`ForeignKey <piccolo.columns.column_types.ForeignKey>` to
    specify the behaviour when a related row is deleted.
    """

    cascade = "CASCADE"
    restrict = "RESTRICT"
    no_action = "NO ACTION"
    set_null = "SET NULL"
    set_default = "SET DEFAULT"

    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __repr__(self):
        return self.__str__()


class OnUpdate(str, Enum):
    """
    Used by :class:`ForeignKey <piccolo.columns.column_types.ForeignKey>` to
    specify the behaviour when a related row is updated.
    """

    cascade = "CASCADE"
    restrict = "RESTRICT"
    no_action = "NO ACTION"
    set_null = "SET NULL"
    set_default = "SET DEFAULT"

    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"

    def __repr__(self):
        return self.__str__()


@dataclass
class ForeignKeyMeta:
    references: t.Union[t.Type[Table], LazyTableReference]
    on_delete: OnDelete
    on_update: OnUpdate
    target_column: t.Union[Column, str, None]
    proxy_columns: t.List[Column] = field(default_factory=list)

    @property
    def resolved_references(self) -> t.Type[Table]:
        """
        Evaluates the ``references`` attribute if it's a ``LazyTableReference``,
        raising a ``ValueError`` if it fails, otherwise returns a ``Table``
        subclass.
        """  # noqa: E501
        from piccolo.table import Table

        if isinstance(self.references, LazyTableReference):
            return self.references.resolve()
        elif inspect.isclass(self.references) and issubclass(
            self.references, Table
        ):
            return self.references
        else:
            raise ValueError(
                "The references attribute is neither a Table subclass or a "
                "LazyTableReference instance."
            )

    @property
    def resolved_target_column(self) -> Column:
        if self.target_column is None:
            return self.resolved_references._meta.primary_key
        elif isinstance(self.target_column, Column):
            return self.resolved_references._meta.get_column_by_name(
                self.target_column._meta.name
            )
        elif isinstance(self.target_column, str):
            return self.resolved_references._meta.get_column_by_name(
                self.target_column
            )
        else:
            raise ValueError("Unable to resolve target_column.")

    def copy(self) -> ForeignKeyMeta:
        kwargs = self.__dict__.copy()
        kwargs.update(proxy_columns=self.proxy_columns.copy())
        return self.__class__(**kwargs)

    def __copy__(self) -> ForeignKeyMeta:
        return self.copy()

    def __deepcopy__(self, memo) -> ForeignKeyMeta:
        """
        We override deepcopy, as it's too slow if it has to recreate
        everything.
        """
        return self.copy()


@dataclass
class ColumnMeta:
    """
    We store as many attributes in ColumnMeta as possible, to help avoid name
    clashes with user defined attributes.
    """

    # General attributes:
    null: bool = False
    primary_key: bool = False
    unique: bool = False
    index: bool = False
    index_method: IndexMethod = IndexMethod.btree
    required: bool = False
    help_text: t.Optional[str] = None
    choices: t.Optional[t.Type[Enum]] = None
    secret: bool = False
    auto_update: t.Any = ...

    # Used for representing the table in migrations and the playground.
    params: t.Dict[str, t.Any] = field(default_factory=dict)

    ###########################################################################

    # Lets you to map a column to a database column with a different name.
    _db_column_name: t.Optional[str] = None

    @property
    def db_column_name(self) -> str:
        return self._db_column_name or self.name

    @db_column_name.setter
    def db_column_name(self, value: str):
        self._db_column_name = value

    ###########################################################################

    # Set by the Table Metaclass:
    _name: t.Optional[str] = None
    _table: t.Optional[t.Type[Table]] = None

    @property
    def name(self) -> str:
        if not self._name:
            raise ValueError(
                "`_name` isn't defined - the Table Metaclass should set it."
            )
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def table(self) -> t.Type[Table]:
        if not self._table:
            raise ValueError(
                "`_table` isn't defined - the Table Metaclass should set it."
            )
        return self._table

    ###########################################################################

    # Used by Foreign Keys:
    call_chain: t.List["ForeignKey"] = field(default_factory=list)
    table_alias: t.Optional[str] = None

    ###########################################################################

    @property
    def engine_type(self) -> str:
        engine = self.table._meta.db
        if engine:
            return engine.engine_type
        else:
            raise ValueError("The table has no engine defined.")

    def get_choices_dict(self) -> t.Optional[t.Dict[str, t.Any]]:
        """
        Return the choices Enum as a dict. It maps the attribute name to a
        dict containing the display name, and value.
        """
        if self.choices is None:
            return None
        output = {}
        for element in self.choices:
            if isinstance(element.value, Choice):
                display_name = element.value.display_name
                value = element.value.value
            else:
                display_name = element.name.replace("_", " ").title()
                value = element.value

            output[element.name] = {
                "display_name": display_name,
                "value": value,
            }

        return output

    ###########################################################################

    def get_default_alias(self):
        column_name = self.db_column_name

        if self.call_chain:
            column_name = (
                "$".join(
                    t.cast(str, i._meta.db_column_name)
                    for i in self.call_chain
                )
                + f"${column_name}"
            )

        return column_name

    def _get_path(self, include_quotes: bool = False):
        column_name = self.db_column_name

        if self.call_chain:
            table_alias = self.call_chain[-1]._meta.table_alias
            if include_quotes:
                return f'"{table_alias}"."{column_name}"'
            else:
                return f"{table_alias}.{column_name}"
        else:
            if include_quotes:
                return f'"{self.table._meta.tablename}"."{column_name}"'
            else:
                return f"{self.table._meta.tablename}.{column_name}"

    def get_full_name(
        self, with_alias: bool = True, include_quotes: bool = True
    ) -> str:
        """
        Returns the full column name, taking into account joins.

        :param with_alias:
            Examples:

            .. code-block python::

                >>> Band.manager.name._meta.get_full_name(with_alias=False)
                'band$manager.name'

                >>> Band.manager.name._meta.get_full_name(with_alias=True)
                'band$manager.name AS "manager$name"'

        :param include_quotes:
            If you're using the name in a SQL query, each component needs to be
            surrounded by double quotes, in case the table or column name
            clashes with a reserved SQL keyword (for example, a column called
            ``order``).

            .. code-block python::

                >>> column._meta.get_full_name(include_quotes=True)
                '"my_table_name"."my_column_name"'

                >>> column._meta.get_full_name(include_quotes=False)
                'my_table_name.my_column_name'


        """
        full_name = self._get_path(include_quotes=include_quotes)

        if with_alias and self.call_chain:
            alias = self.get_default_alias()
            if include_quotes:
                full_name += f' AS "{alias}"'
            else:
                full_name += f" AS {alias}"

        return full_name

    ###########################################################################

    def copy(self) -> ColumnMeta:
        kwargs = self.__dict__.copy()
        kwargs.update(
            params=self.params.copy(),
            call_chain=self.call_chain.copy(),
        )

        # Make sure we don't accidentally include any other attributes which
        # aren't supported by the constructor.
        field_names = [i.name for i in fields(self.__class__)]
        kwargs = {
            kwarg: value
            for kwarg, value in kwargs.items()
            if kwarg in field_names
        }

        return self.__class__(**kwargs)

    def __copy__(self) -> ColumnMeta:
        return self.copy()

    def __deepcopy__(self, memo) -> ColumnMeta:
        """
        We override deepcopy, as it's too slow if it has to recreate
        everything.
        """
        return self.copy()


class Selectable(metaclass=ABCMeta):
    """
    Anything which inherits from this can be used in a select query.
    """

    _alias: t.Optional[str]

    @abstractmethod
    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        """
        In a query, what to output after the select statement - could be a
        column name, a sub query, a function etc. For a column it will be the
        column name.
        """
        raise NotImplementedError()

    def as_alias(self, alias: str) -> Selectable:
        """
        Allows column names to be changed in the result of a select.
        """
        self._alias = alias
        return self


class Column(Selectable):
    """
    All other columns inherit from ``Column``. Don't use it directly.

    The following arguments apply to all column types:

    :param null:
        Whether the column is nullable.

    :param primary_key:
        If set, the column is used as a primary key.

    :param default:
        The column value to use if not specified by the user.

    :param unique:
        If set, a unique constraint will be added to the column.

    :param index:
        Whether an index is created for the column, which can improve
        the speed of selects, but can slow down inserts.

    :param index_method:
        If index is set to ``True``, this specifies what type of index is
        created.

    :param required:
        This isn't used by the database - it's to indicate to other tools that
        the user must provide this value. Example uses are in serialisers for
        API endpoints, and form fields.

    :param help_text:
        This provides some context about what the column is being used for. For
        example, for a ``Decimal`` column called ``value``, it could say
        ``'The units are millions of dollars'``. The database doesn't use this
        value, but tools such as Piccolo Admin use it to show a tooltip in the
        GUI.

    :param choices:
        An optional Enum - when specified, other tools such as Piccolo Admin
        will render the available options in the GUI.

    :param db_column_name:
        If specified, you can override the name used for the column in the
        database. The main reason for this is when using a legacy database,
        with a problematic column name (for example ``'class'``, which is a
        reserved Python keyword). Here's an example:

        .. code-block:: python

            class MyTable(Table):
                class_ = Varchar(db_column_name="class")

            >>> await MyTable.select(MyTable.class_)
            [{'id': 1, 'class': 'test'}]

        This is an advanced feature which you should only need in niche
        situations.

    :param secret:
        If ``secret=True`` is specified, it allows a user to automatically
        omit any fields when doing a select query, to help prevent
        inadvertent leakage of sensitive data.

        .. code-block:: python

            class Band(Table):
                name = Varchar()
                net_worth = Integer(secret=True)

            >>> await Band.select(exclude_secrets=True)
            [{'name': 'Pythonistas'}]

    :param auto_update:
        Allows you to specify a value to set this column to each time it is
        updated (via ``MyTable.update``, or ``MyTable.save`` on an existing
        row). A common use case is having a ``modified_on`` column.

        .. code-block:: python

            class Band(Table):
                name = Varchar()
                popularity = Integer()
                # The value can be a function or static value:
                modified_on = Timestamp(auto_update=datetime.datetime.now)

            # This will automatically set the `modified_on` column to the
            # current timestamp, without having to explicitly set it:
            >>> await Band.update({
            ...     Band.popularity: Band.popularity + 100
            ... }).where(Band.name == 'Pythonistas')

        Note - this feature is implemented purely within the ORM. If you want
        similar functionality on the database level (i.e. if you plan on using
        raw SQL to perform updates), then you may be better off creating SQL
        triggers instead.

    """

    value_type: t.Type = int

    def __init__(
        self,
        null: bool = False,
        primary_key: bool = False,
        unique: bool = False,
        index: bool = False,
        index_method: IndexMethod = IndexMethod.btree,
        required: bool = False,
        help_text: t.Optional[str] = None,
        choices: t.Optional[t.Type[Enum]] = None,
        db_column_name: t.Optional[str] = None,
        secret: bool = False,
        auto_update: t.Any = ...,
        **kwargs,
    ) -> None:
        # This is for backwards compatibility - originally there were two
        # separate arguments `primary` and `key`, but they have now been merged
        # into `primary_key`.
        if (kwargs.get("primary") is True) and (kwargs.get("key") is True):
            primary_key = True

        # Used for migrations.
        # We deliberately omit 'required', 'auto_update' and 'help_text' as
        # they don't effect the actual schema.
        # 'choices' isn't used directly in the schema, but may be important
        # for data migrations.
        kwargs.update(
            {
                "null": null,
                "primary_key": primary_key,
                "unique": unique,
                "index": index,
                "index_method": index_method,
                "choices": choices,
                "db_column_name": db_column_name,
                "secret": secret,
            }
        )

        if choices is not None:
            self._validate_choices(choices, allowed_type=self.value_type)

        self._meta = ColumnMeta(
            null=null,
            primary_key=primary_key,
            unique=unique,
            index=index,
            index_method=index_method,
            params=kwargs,
            required=required,
            help_text=help_text,
            choices=choices,
            _db_column_name=db_column_name,
            secret=secret,
            auto_update=auto_update,
        )

        self._alias: t.Optional[str] = None

    def _validate_default(
        self,
        default: t.Any,
        allowed_types: t.Iterable[t.Union[None, t.Type[t.Any]]],
        allow_recursion: bool = True,
    ) -> bool:
        """
        Make sure that the default value is of the allowed types.
        """
        if getattr(self, "_validated", None):
            # If it has previously been validated by a subclass, don't
            # validate again.
            return True
        elif (
            default is None
            and None in allowed_types
            or type(default) in allowed_types
        ):
            self._validated = True
            return True
        elif callable(default):
            # We need to prevent recursion, otherwise a function which returns
            # a function would be an infinite loop.
            if allow_recursion and self._validate_default(
                default(), allowed_types=allowed_types, allow_recursion=False
            ):
                self._validated = True
                return True
        elif (
            isinstance(default, Enum) and type(default.value) in allowed_types
        ):
            self._validated = True
            return True

        raise ValueError(
            f"The default {default} isn't one of the permitted types - "
            f"{allowed_types}"
        )

    def _validate_choices(
        self, choices: t.Type[Enum], allowed_type: t.Type[t.Any]
    ) -> bool:
        """
        Make sure the choices value has values of the allowed_type.
        """
        if getattr(self, "_validated_choices", None):
            # If it has previously been validated by a subclass, don't
            # validate again.
            return True

        for element in choices:
            if isinstance(element.value, allowed_type):
                continue
            elif isinstance(element.value, Choice) and isinstance(
                element.value.value, allowed_type
            ):
                continue
            else:
                raise ValueError(
                    f"{element.name} doesn't have the correct type"
                )

        self._validated_choices = True

        return True

    def is_in(self, values: t.List[t.Any]) -> Where:
        if len(values) == 0:
            raise ValueError(
                "The `values` list argument must contain at least one value."
            )
        return Where(column=self, values=values, operator=In)

    def not_in(self, values: t.List[t.Any]) -> Where:
        if len(values) == 0:
            raise ValueError(
                "The `values` list argument must contain at least one value."
            )
        return Where(column=self, values=values, operator=NotIn)

    def like(self, value: str) -> Where:
        """
        Both SQLite and Postgres support LIKE, but they mean different things.

        In Postgres, LIKE is case sensitive (i.e. 'foo' equals 'foo', but
        'foo' doesn't equal 'Foo').

        In SQLite, LIKE is case insensitive for ASCII characters
        (i.e. 'foo' equals 'Foo'). But not for non-ASCII characters. To learn
        more, see the docs:

        https://sqlite.org/lang_expr.html#the_like_glob_regexp_and_match_operators

        """
        return Where(column=self, value=value, operator=Like)

    def ilike(self, value: str) -> Where:
        """
        Only Postgres supports ILIKE. It's used for case insensitive matching.

        For SQLite, it's just proxied to a LIKE query instead.

        """
        if self._meta.engine_type in ("postgres", "cockroach"):
            operator: t.Type[ComparisonOperator] = ILike
        else:
            colored_warning(
                "SQLite doesn't support ILIKE, falling back to LIKE."
            )
            operator = Like
        return Where(column=self, value=value, operator=operator)

    def not_like(self, value: str) -> Where:
        return Where(column=self, value=value, operator=NotLike)

    def __lt__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessThan)

    def __le__(self, value) -> Where:
        return Where(column=self, value=value, operator=LessEqualThan)

    def __gt__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterThan)

    def __ge__(self, value) -> Where:
        return Where(column=self, value=value, operator=GreaterEqualThan)

    def _equals(self, column: Column, including_joins: bool = False) -> bool:
        """
        We override ``__eq__``, in order to do queries such as:

        .. code-block:: python

            await Band.select().where(Band.name == 'Pythonistas')

        But this means that comparisons such as this can give unexpected
        results:

        .. code-block:: python

            # We would expect the answer to be `True`, but we get `Where`
            # instead:
            >>> MyTable.some_column == MyTable.some_column
            <Where>

        Also, column comparison is sometimes more complex than it appears. This
        is why we have this custom method for comparing columns.

        Take this example:

        .. code-block:: python

            Band.manager.name == Manager.name

        They both refer to the ``name`` column on the ``Manager`` table, except
        one has joins and the other doesn't.

        :param including_joins:
            If ``True``, then we check if the columns are the same, as well as
            their joins, i.e. ``Band.manager.name`` != ``Manager.name``.

        """
        if isinstance(column, Column):
            if (
                self._meta.name == column._meta.name
                and self._meta.table._meta.tablename
                == column._meta.table._meta.tablename
            ):
                if including_joins:
                    if len(column._meta.call_chain) == len(
                        self._meta.call_chain
                    ):
                        return all(
                            column_a._equals(column_b, including_joins=False)
                            for column_a, column_b in zip(
                                column._meta.call_chain,
                                self._meta.call_chain,
                            )
                        )

                else:
                    return True

        return False

    def __eq__(self, value) -> Where:  # type: ignore[override]
        if value is None:
            return Where(column=self, operator=IsNull)
        else:
            return Where(column=self, value=value, operator=Equal)

    def __ne__(self, value) -> Where:  # type: ignore[override]
        if value is None:
            return Where(column=self, operator=IsNotNull)
        else:
            return Where(column=self, value=value, operator=NotEqual)

    def __hash__(self):
        return hash(self._meta.name)

    def is_null(self) -> Where:
        """
        Can be used instead of ``MyTable.column == None``, because some linters
        don't like a comparison to ``None``.
        """
        return Where(column=self, operator=IsNull)

    def is_not_null(self) -> Where:
        """
        Can be used instead of ``MyTable.column != None``, because some linters
        don't like a comparison to ``None``.
        """
        return Where(column=self, operator=IsNotNull)

    def as_alias(self, name: str) -> Column:
        """
        Allows column names to be changed in the result of a select.

        For example:

        .. code-block:: python

            >>> await Band.select(Band.name.as_alias('title')).run()
            {'title': 'Pythonistas'}

        """
        column = copy.deepcopy(self)
        column._alias = name
        return column

    def get_default_value(self) -> t.Any:
        """
        If the column has a default attribute, return it. If it's callable,
        return the response instead.
        """
        default = getattr(self, "default", ...)
        if default is not ...:
            default = default.value if isinstance(default, Enum) else default
            is_callable = hasattr(default, "__call__")
            return default() if is_callable else default  # type: ignore
        return None

    def get_select_string(
        self, engine_type: str, with_alias: bool = True
    ) -> str:
        """
        How to refer to this column in a SQL query, taking account of any joins
        and aliases.
        """
        if with_alias:
            if self._alias:
                original_name = self._meta.get_full_name(
                    with_alias=False,
                )
                return f'{original_name} AS "{self._alias}"'
            else:
                return self._meta.get_full_name(
                    with_alias=True,
                )

        return self._meta.get_full_name(with_alias=False)

    def get_where_string(self, engine_type: str) -> str:
        return self.get_select_string(
            engine_type=engine_type, with_alias=False
        )

    def get_sql_value(self, value: t.Any) -> t.Any:
        """
        When using DDL statements, we can't parameterise the values. An example
        is when setting the default for a column. So we have to convert from
        the Python type to a string representation which we can include in our
        DDL statements.

        :param value:
            The Python value to convert to a string usable in a DDL statement
            e.g. 1.
        :returns:
            The string usable in the DDL statement e.g. '1'.

        """
        if isinstance(value, Default):
            return getattr(value, self._meta.engine_type)
        elif value is None:
            return "null"
        elif isinstance(value, (float, decimal.Decimal)):
            return str(value)
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, datetime.datetime):
            return f"'{value.isoformat().replace('T', ' ')}'"
        elif isinstance(value, datetime.date):
            return f"'{value.isoformat()}'"
        elif isinstance(value, datetime.time):
            return f"'{value.isoformat()}'"
        elif isinstance(value, datetime.timedelta):
            interval = IntervalCustom.from_timedelta(value)
            return getattr(interval, self._meta.engine_type)
        elif isinstance(value, bytes):
            return f"'{value.hex()}'"
        elif isinstance(value, uuid.UUID):
            return f"'{value}'"
        elif isinstance(value, list):
            # Convert to the array syntax.
            return (
                "'{"
                + ", ".join(
                    f'"{i}"'
                    if isinstance(i, str)
                    else str(self.get_sql_value(i))
                    for i in value
                )
            ) + "}'"
        else:
            return value

    @property
    def column_type(self):
        return self.__class__.__name__.upper()

    @property
    def ddl(self) -> str:
        """
        Used when creating tables.
        """
        query = f'"{self._meta.db_column_name}" {self.column_type}'
        if self._meta.primary_key:
            query += " PRIMARY KEY"
        if self._meta.unique:
            query += " UNIQUE"
        if not self._meta.null:
            query += " NOT NULL"

        foreign_key_meta: t.Optional[ForeignKeyMeta] = getattr(
            self, "_foreign_key_meta", None
        )
        if foreign_key_meta:
            references = foreign_key_meta.resolved_references
            tablename = references._meta.tablename
            on_delete = foreign_key_meta.on_delete.value
            on_update = foreign_key_meta.on_update.value
            target_column_name = (
                foreign_key_meta.resolved_target_column._meta.name
            )
            query += (
                f" REFERENCES {tablename} ({target_column_name})"
                f" ON DELETE {on_delete}"
                f" ON UPDATE {on_update}"
            )

        # Always ran for Cockroach because unique_rowid() is directly
        # defined for Cockroach Serial and BigSerial.
        # Postgres and SQLite will not run this for Serial and BigSerial.
        if self._meta.engine_type in (
            "cockroach"
        ) or self.__class__.__name__ not in ("Serial", "BigSerial"):
            default = self.get_default_value()
            sql_value = self.get_sql_value(value=default)
            query += f" DEFAULT {sql_value}"

        return query

    def copy(self) -> Column:
        column: Column = copy.copy(self)
        column._meta = self._meta.copy()
        return column

    def __deepcopy__(self, memo) -> Column:
        """
        We override deepcopy, as it's too slow if it has to recreate
        everything.
        """
        return self.copy()

    def __str__(self):
        return self.ddl.__str__()

    def __repr__(self):
        try:
            table = self._meta.table
        except ValueError:
            table_class_name = "Unknown"
        else:
            table_class_name = table.__name__
        return (
            f"{table_class_name}.{self._meta.name} - "
            f"{self.__class__.__name__}"
        )
