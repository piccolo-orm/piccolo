from __future__ import annotations
import copy
from datetime import datetime, date, time
import decimal
import typing as t
import uuid

from piccolo.columns.base import Column, OnDelete, OnUpdate, ForeignKeyMeta
from piccolo.columns.operators.string import ConcatPostgres, ConcatSQLite
from piccolo.columns.defaults.date import DateArg, DateNow, DateCustom
from piccolo.columns.defaults.time import TimeArg, TimeNow, TimeCustom
from piccolo.columns.defaults.timestamp import (
    TimestampArg,
    TimestampNow,
    TimestampCustom,
)
from piccolo.columns.defaults.uuid import UUIDArg, UUID4
from piccolo.querystring import Unquoted, QueryString

if t.TYPE_CHECKING:
    from piccolo.table import Table


###############################################################################


class ConcatDelegate:
    """
    Used in update queries to concatenate two strings - for example:

    await Band.update({Band.name: Band.name + 'abc'}).run()
    """

    def get_querystring(
        self,
        column_name: str,
        value: t.Union[str, Varchar, Text],
        engine_type: str,
        reverse=False,
    ):
        Concat = ConcatPostgres if engine_type == "postgres" else ConcatSQLite

        if isinstance(value, (Varchar, Text)):
            column: Column = value
            if len(column._meta.call_chain) > 0:
                raise ValueError(
                    "Adding values across joins isn't currently supported."
                )
            other_column_name = column._meta.name
            if reverse:
                return QueryString(
                    Concat.template.format(
                        value_1=other_column_name, value_2=column_name
                    )
                )
            else:
                return QueryString(
                    Concat.template.format(
                        value_1=column_name, value_2=other_column_name
                    )
                )
        elif isinstance(value, str):
            if reverse:
                value_1 = QueryString("CAST({} AS text)", value)
                return QueryString(
                    Concat.template.format(value_1="{}", value_2=column_name),
                    value_1,
                )
            else:
                value_2 = QueryString("CAST({} AS text)", value)
                return QueryString(
                    Concat.template.format(value_1=column_name, value_2="{}"),
                    value_2,
                )
        else:
            raise ValueError(
                "Only str, Varchar columns, and Text columns can be added."
            )


class MathDelegate:
    """
    Used in update queries to perform math operations on columns, for example:

    await Band.update({Band.popularity: Band.popularity + 100}).run()
    """

    def get_querystring(
        self,
        column_name: str,
        operator: str,
        value: t.Union[int, float, Integer],
        reverse=False,
    ):
        if isinstance(value, Integer):
            column: Integer = value
            if len(column._meta.call_chain) > 0:
                raise ValueError(
                    "Adding values across joins isn't currently supported."
                )
            column_name = column._meta.name
            if reverse:
                return QueryString(f"{column_name} {operator} {column_name}")
            else:
                return QueryString(f"{column_name} {operator} {column_name}")
        elif isinstance(value, (int, float)):
            if reverse:
                return QueryString(f"{{}} {operator} {column_name}", value)
            else:
                return QueryString(f"{column_name} {operator} {{}}", value)
        else:
            raise ValueError(
                "Only integers, floats, and other Integer columns can be "
                "added."
            )


###############################################################################


class Varchar(Column):
    """
    Used for storing text when you want to enforce character length limits.
    Uses the ``str`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            name = Varchar(length=100)

        # Create
        >>> Band(name='Pythonistas').save().run_sync()

        # Query
        >>> Band.select(Band.name).run_sync()
        {'name': 'Pythonistas'}

    :param length:
        The maximum number of characters allowed.

    """

    value_type = str
    concat_delegate: ConcatDelegate = ConcatDelegate()

    def __init__(
        self, length: int = 255, default: t.Union[str, None] = "", **kwargs
    ) -> None:
        self._validate_default(default, (str, None))

        self.length = length
        self.default = default
        kwargs.update({"length": length, "default": default})
        super().__init__(**kwargs)

    @property
    def column_type(self):
        if self.length:
            return f"VARCHAR({self.length})"
        else:
            return "VARCHAR"

    def __add__(self, value: t.Union[str, Varchar, Text]) -> QueryString:
        engine_type = self._meta.table._meta.db.engine_type
        return self.concat_delegate.get_querystring(
            column_name=self._meta.name, value=value, engine_type=engine_type,
        )

    def __radd__(self, value: t.Union[str, Varchar, Text]) -> QueryString:
        engine_type = self._meta.table._meta.db.engine_type
        return self.concat_delegate.get_querystring(
            column_name=self._meta.name,
            value=value,
            engine_type=engine_type,
            reverse=True,
        )


class Secret(Varchar):
    """
    The database treats it the same as a ``Varchar``, but Piccolo may treat it
    differently internally - for example, allowing a user to automatically
    omit any secret fields when doing a select query, to help prevent
    inadvertant leakage. A common use for a ``Secret`` field is a password.

    Uses the ``str`` type for values.

    **Example**

    .. code-block:: python

        class Door(Table):
            code = Secret(length=100)

        # Create
        >>> Door(code='123abc').save().run_sync()

        # Query
        >>> Door.select(Door.code).run_sync()
        {'code': '123abc'}

    """

    pass


class Text(Column):
    """
    Use when you want to store large strings, and don't want to limit the
    string size. Uses the ``str`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            name = Text()

        # Create
        >>> Band(name='Pythonistas').save().run_sync()

        # Query
        >>> Band.select(Band.name).run_sync()
        {'name': 'Pythonistas'}

    """

    value_type = str
    concat_delegate: ConcatDelegate = ConcatDelegate()

    def __init__(self, default: t.Union[str, None] = "", **kwargs) -> None:
        self._validate_default(default, (str, None))
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)

    def __add__(self, value: t.Union[str, Varchar, Text]) -> QueryString:
        engine_type = self._meta.table._meta.db.engine_type
        return self.concat_delegate.get_querystring(
            column_name=self._meta.name, value=value, engine_type=engine_type
        )

    def __radd__(self, value: t.Union[str, Varchar, Text]) -> QueryString:
        engine_type = self._meta.table._meta.db.engine_type
        return self.concat_delegate.get_querystring(
            column_name=self._meta.name,
            value=value,
            engine_type=engine_type,
            reverse=True,
        )


class UUID(Column):
    """
    Used for storing UUIDs - in Postgres a UUID column type is used, and in
    SQLite it's just a Varchar. Uses the ``uuid.UUID`` type for values.

    **Example**

    .. code-block:: python

        import uuid

        class Band(Table):
            uuid = UUID()

        # Create
        >>> DiscountCode(code=uuid.uuid4()).save().run_sync()

        # Query
        >>> DiscountCode.select(DiscountCode.code).run_sync()
        {'code': UUID('09c4c17d-af68-4ce7-9955-73dcd892e462')}

    """

    value_type = uuid.UUID

    def __init__(self, default: UUIDArg = UUID4(), **kwargs) -> None:
        self._validate_default(default, UUIDArg.__args__)  # type: ignore

        if default == uuid.uuid4:
            default = UUID4()

        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Integer(Column):
    """
    Used for storing whole numbers. Uses the ``int`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            popularity = Integer()

        # Create
        >>> Band(popularity=1000).save().run_sync()

        # Query
        >>> Band.select(Band.popularity).run_sync()
        {'popularity': 1000}

    """

    math_delegate = MathDelegate()

    def __init__(self, default: t.Union[int, None] = 0, **kwargs) -> None:
        self._validate_default(default, (int, None))
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)

    def __add__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name, operator="+", value=value
        )

    def __radd__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name,
            operator="+",
            value=value,
            reverse=True,
        )

    def __sub__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name, operator="-", value=value
        )

    def __rsub__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name,
            operator="-",
            value=value,
            reverse=True,
        )

    def __mul__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name, operator="*", value=value
        )

    def __rmul__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name,
            operator="*",
            value=value,
            reverse=True,
        )

    def __truediv__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name, operator="/", value=value
        )

    def __rtruediv__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name,
            operator="/",
            value=value,
            reverse=True,
        )

    def __floordiv__(self, value: t.Union[int, float, Integer]) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name, operator="/", value=value
        )

    def __rfloordiv__(
        self, value: t.Union[int, float, Integer]
    ) -> QueryString:
        return self.math_delegate.get_querystring(
            column_name=self._meta.name,
            operator="/",
            value=value,
            reverse=True,
        )


###############################################################################
# BigInt and SmallInt only exist on Postgres. SQLite treats them the same as
# Integer columns.


class BigInt(Integer):
    """
    In Postgres, this column supports large integers. In SQLite, it's an alias
    to an Integer column, which already supports large integers. Uses the
    ``int`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            value = BigInt()

        # Create
        >>> Band(popularity=1000000).save().run_sync()

        # Query
        >>> Band.select(Band.popularity).run_sync()
        {'popularity': 1000000}

    """

    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "BIGINT"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")


class SmallInt(Integer):
    """
    In Postgres, this column supports small integers. In SQLite, it's an alias
    to an Integer column. Uses the ``int`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            value = SmallInt()

        # Create
        >>> Band(popularity=1000).save().run_sync()

        # Query
        >>> Band.select(Band.popularity).run_sync()
        {'popularity': 1000}

    """

    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "SMALLINT"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")


###############################################################################


class Serial(Column):
    """
    An alias to an autoincremenring integer column in Postgres.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


DEFAULT = Unquoted("DEFAULT")
NULL = Unquoted("null")


class PrimaryKey(Column):
    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "SERIAL"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")

    def default(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return DEFAULT
        elif engine_type == "sqlite":
            return NULL
        raise Exception("Unrecognized engine type")

    def __init__(self, **kwargs) -> None:
        # Set the index to False, as a database should automatically create
        # an index for a PrimaryKey column.
        kwargs.update({"primary": True, "key": True, "index": False})
        super().__init__(**kwargs)


###############################################################################


class Timestamp(Column):
    """
    Used for storing datetimes. Uses the ``datetime`` type for values.

    **Example**

    .. code-block:: python

        import datetime

        class Concert(Table):
            starts = Timestamp()

        # Create
        >>> Concert(starts=datetime.datetime(year=2050, month=1, day=1)).save().run_sync()

        # Query
        >>> Concert.select(Concert.starts).run_sync()
        {'starts': datetime.datetime(2050, 1, 1, 0, 0)}

    """

    value_type = datetime

    def __init__(
        self, default: TimestampArg = TimestampNow(), **kwargs
    ) -> None:
        self._validate_default(default, TimestampArg.__args__)  # type: ignore

        if isinstance(default, datetime):
            default = TimestampCustom.from_datetime(default)

        if default == datetime.now:
            default = TimestampNow()

        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Date(Column):
    """
    Used for storing dates. Uses the ``date`` type for values.

    **Example**

    .. code-block:: python

        import datetime

        class Concert(Table):
            starts = Date()

        # Create
        >>> Concert(
        >>>     starts=datetime.date(year=2020, month=1, day=1)
        >>> ).save().run_sync()

        # Query
        >>> Concert.select(Concert.starts).run_sync()
        {'starts': datetime.date(2020, 1, 1)}

    """

    value_type = date

    def __init__(self, default: DateArg = DateNow(), **kwargs) -> None:
        self._validate_default(default, DateArg.__args__)  # type: ignore

        if isinstance(default, date):
            default = DateCustom.from_date(default)

        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Time(Column):
    """
    Used for storing times. Uses the ``time`` type for values.

    **Example**

    .. code-block:: python

        import datetime

        class Concert(Table):
            starts = Time()

        # Create
        >>> Concert(starts=datetime.time(hour=20, minute=0, second=0)).save().run_sync()

        # Query
        >>> Concert.select(Concert.starts).run_sync()
        {'starts': datetime.time(20, 0, 0)}

    """

    value_type = time

    def __init__(self, default: TimeArg = TimeNow(), **kwargs) -> None:
        self._validate_default(default, TimeArg.__args__)  # type: ignore

        if isinstance(default, time):
            default = TimeCustom.from_time(default)

        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


###############################################################################


class Boolean(Column):
    """
    Used for storing True / False values. Uses the ``bool`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            has_drummer = Boolean()

        # Create
        >>> Band(has_drummer=True).save().run_sync()

        # Query
        >>> Band.select(Band.has_drummer).run_sync()
        {'has_drummer': True}

    """

    value_type = bool

    def __init__(self, default: t.Union[bool, None] = False, **kwargs) -> None:
        self._validate_default(default, (bool, None))
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


###############################################################################


class Numeric(Column):
    """
    Used for storing decimal numbers, when precision is important. An example
    use case is storing financial data. The value is returned as a ``Decimal``.

    **Example**

    .. code-block:: python

        from decimal import Decimal

        class Ticket(Table):
            price = Numeric(digits=(5,2))

        # Create
        >>> Ticket(price=Decimal('50.0')).save().run_sync()

        # Query
        >>> Ticket.select(Ticket.price).run_sync()
        {'price': Decimal('50.0')}

    :arg digits:
        When creating the column, you specify how many digits are allowed
        using a tuple. The first value is the `precision`, which is the
        total number of digits allowed. The second value is the `range`,
        which specifies how many of those digits are after the decimal
        point. For example, to store monetary values up to £999.99, the
        digits argument is `(5,2)`.

    """

    value_type = decimal.Decimal

    @property
    def column_type(self):
        if self.digits:
            return f"NUMERIC({self.precision}, {self.scale})"
        else:
            return "NUMERIC"

    @property
    def precision(self):
        """
        The total number of digits allowed.
        """
        return self.digits[0]

    @property
    def scale(self):
        """
        The number of digits after the decimal point.
        """
        return self.digits[1]

    def __init__(
        self,
        digits: t.Optional[t.Tuple[int, int]] = None,
        default: t.Union[decimal.Decimal, None] = decimal.Decimal(0.0),
        **kwargs,
    ) -> None:
        if isinstance(digits, tuple):
            if len(digits) != 2:
                raise ValueError(
                    "The `digits` argument should be a tuple of length 2, "
                    "with the first value being the precision, and the second "
                    "value being the scale."
                )
        else:
            if digits is not None:
                raise ValueError("The digits argument should be a tuple.")

        self._validate_default(default, (decimal.Decimal, None))

        self.default = default
        self.digits = digits
        kwargs.update({"default": default, "digits": digits})
        super().__init__(**kwargs)


class Decimal(Numeric):
    """
    An alias for Numeric.
    """

    pass


class Real(Column):
    """
    Can be used instead of ``Numeric`` for storing numbers, when precision
    isn't as important. The ``float`` type is used for values.

    **Example**

    .. code-block:: python

        class Concert(Table):
            rating = Real()

        # Create
        >>> Concert(rating=7.8).save().run_sync()

        # Query
        >>> Concert.select(Concert.rating).run_sync()
        {'rating': 7.8}

    """

    value_type = float

    def __init__(self, default: t.Union[float, None] = 0.0, **kwargs) -> None:
        self._validate_default(default, (float, None))
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Float(Real):
    """
    An alias for Real.
    """

    pass


###############################################################################


class ForeignKey(Integer):
    """
    Used to reference another table. Uses the ``int`` type for values.

    **Example**

    .. code-block:: python

        class Band(Table):
            manager = ForeignKey(references=Manager)

        # Create
        >>> Band(manager=1).save().run_sync()

        # Query
        >>> Band.select(Band.manager).run_sync()
        {'manager': 1}

        # Query object
        >>> band = await Band.objects().first().run()
        >>> band.manager
        1

    **Joins**

    Can also use it to perform joins:

    .. code-block:: python

        >>> await Band.select(Band.name, Band.manager.name).first().run()
        {'name': 'Pythonistas', 'manager.name': 'Guido'}

    To get a referenced row as an object:

    .. code-block:: python

        manager = await Manager.objects().where(
            Manager.id == some_band.manager
        ).run()

    Or use either of the following, which are just a proxy to the above:

    .. code-block:: python

        manager = await band.get_related('manager').run()
        manager = await band.get_related(Band.manager).run()

    To change the manager:

    .. code-block:: python

        band.manager = some_manager_id
        await band.save().run()

    :param references:
        The ``Table`` being referenced.

        A table can have a reference to itself, if you pass a ``references``
        argument of ``'self'``.

        .. code-block:: python

            class Musician(Table):
                name = Varchar(length=100)
                instructor = ForeignKey(references='self')

    :param on_delete:
        Determines what the database should do when a row is deleted with
        foreign keys referencing it. If set to ``OnDelete.cascade``, any rows
        referencing the deleted row are also deleted.

        Options:

            * ``OnDelete.cascade`` (default)
            * ``OnDelete.restrict``
            * ``OnDelete.no_action``
            * ``OnDelete.set_null``
            * ``OnDelete.set_default``

        To learn more about the different options, see the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK>`_.

        .. code-block:: python

            from piccolo.columns import OnDelete

            class Band(Table):
                name = ForeignKey(references=Manager, on_delete=OnDelete.cascade)

    :param on_update:
        Determines what the database should do when a row has it's primary key
        updated. If set to ``OnDelete.cascade``, any rows referencing the
        updated row will have their references updated to point to the new
        primary key.

        Options:

            * ``OnUpdate.cascade`` (default)
            * ``OnUpdate.restrict``
            * ``OnUpdate.no_action``
            * ``OnUpdate.set_null``
            * ``OnUpdate.set_default``

        To learn more about the different options, see the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK>`_.

        .. code-block:: python

            from piccolo.columns import OnDelete

            class Band(Table):
                name = ForeignKey(references=Manager, on_update=OnUpdate.cascade)

    """

    column_type = "INTEGER"

    def __init__(
        self,
        references: t.Union[t.Type[Table], str],
        default: t.Union[int, None] = None,
        null: bool = True,
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        **kwargs,
    ) -> None:
        self._validate_default(default, (int, None))

        if isinstance(references, str):
            if references != "self":
                raise ValueError(
                    "String values for 'references' currently only supports "
                    "'self', which is a reference to the current table."
                )

        kwargs.update(
            {
                "references": references,
                "on_delete": on_delete,
                "on_update": on_update,
            }
        )
        super().__init__(default=default, null=null, **kwargs)

        if t.TYPE_CHECKING:
            # This is here just for type inference - the actual value is set by
            # the Table metaclass.
            from piccolo.table import Table

            self._foreign_key_meta = ForeignKeyMeta(
                Table, OnDelete.cascade, OnUpdate.cascade
            )

    def __getattribute__(self, name: str):
        """
        Returns attributes unmodified unless they're Column instances, in which
        case a copy is returned with an updated call_chain (which records the
        joins required).
        """
        # see if it has an attribute with that name ...
        # if it's asking for a foreign key ... return a copy of self ...

        try:
            value = object.__getattribute__(self, name)
        except AttributeError:
            raise AttributeError

        foreignkey_class = object.__getattribute__(self, "__class__")

        if isinstance(value, foreignkey_class):  # i.e. a ForeignKey
            new_column = copy.deepcopy(value)
            new_column._meta.call_chain = copy.copy(self._meta.call_chain)
            new_column._meta.call_chain.append(self)

            # We have to set limits to the call chain because Table 1 can
            # reference Table 2, which references Table 1, creating an endless
            # loop. For now an arbitrary limit is set of 10 levels deep.
            # When querying a call chain more than 10 levels deep, an error
            # will be raised. Often there are more effective ways of
            # structuring a query than joining so many tables anyway.
            if len(new_column._meta.call_chain) > 10:
                raise Exception("Call chain too long!")

            for proxy_column in self._foreign_key_meta.proxy_columns:
                try:
                    delattr(new_column, proxy_column._meta.name)
                except Exception:
                    pass

            for column in value._foreign_key_meta.references._meta.columns:
                _column: Column = copy.deepcopy(column)
                _column._meta.call_chain = copy.copy(
                    new_column._meta.call_chain
                )
                _column._meta.call_chain.append(new_column)
                if _column._meta.name == "id":
                    continue
                setattr(new_column, _column._meta.name, _column)
                self._foreign_key_meta.proxy_columns.append(_column)

            return new_column
        elif issubclass(type(value), Column):
            new_column = copy.deepcopy(value)
            new_column._meta.call_chain = copy.copy(self._meta.call_chain)
            new_column._meta.call_chain.append(self)
            return new_column
        else:
            return value
