from __future__ import annotations
import copy
from datetime import datetime
import decimal
import typing as t
import uuid

from piccolo.columns.base import Column, OnDelete, OnUpdate, ForeignKeyMeta
from piccolo.columns.operators.string import ConcatPostgres, ConcatSQLite
from piccolo.querystring import Unquoted, QueryString

if t.TYPE_CHECKING:
    from piccolo.table import Table  # noqa
    from piccolo.custom_types import Datetime  # noqa


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
    Used for text when you want to enforce character length limits.
    """

    value_type = str
    concat_delegate: ConcatDelegate = ConcatDelegate()

    def __init__(self, length: int = 255, default: str = "", **kwargs) -> None:
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
    The database treats it the same as a Varchar, but Piccolo may treat it
    differently internally - for example, allowing a user to automatically
    omit any secret fields when doing a select query, to help prevent
    inadvertant leakage. A common use for a Secret field is a password.
    """

    pass


class Text(Column):
    """
    Used for text when you don't want any character length limits.
    """

    value_type = str
    concat_delegate: ConcatDelegate = ConcatDelegate()

    def __init__(self, default: str = "", **kwargs) -> None:
        self.default = default
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
    Represented in Postgres as a UUID field, and a Varchar field in SQLite.
    """

    value_type = t.Union[str, uuid.UUID]

    def default(self) -> str:
        return str(uuid.uuid4())

    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "UUID"
        elif engine_type == "sqlite":
            return "VARCHAR"
        raise Exception("Unrecognized engine type")


class Integer(Column):

    math_delegate = MathDelegate()

    def __init__(self, default: int = None, **kwargs) -> None:
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
    @property
    def column_type(self):
        engine_type = self._meta.table._meta.db.engine_type
        if engine_type == "postgres":
            return "BIGINT"
        elif engine_type == "sqlite":
            return "INTEGER"
        raise Exception("Unrecognized engine type")


class SmallInt(Integer):
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
        kwargs.update({"primary": True, "key": True})
        super().__init__(**kwargs)


class Timestamp(Column):

    value_type = datetime

    def __init__(self, default: Datetime = None, **kwargs) -> None:
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


class Boolean(Column):

    value_type = bool

    def __init__(self, default: bool = False, **kwargs) -> None:
        self.default = default
        kwargs.update({"default": default})
        super().__init__(**kwargs)


###############################################################################


class Numeric(Column):
    """
    Used to represent values precisely. The value is returned as a Decimal.
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
        default: decimal.Decimal = decimal.Decimal(0.0),
        **kwargs,
    ) -> None:
        if isinstance(digits, tuple) and len(digits) != 2:
            raise ValueError(
                "The `digits` argument should be a tuple of length 2, with "
                "the first value being the precision, and the second value "
                "being the scale."
            )

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
    Can be used instead of Numeric when precision isn't as important. The value
    is returned as a float.
    """

    value_type = float

    def __init__(self, default: float = 0.0, **kwargs) -> None:
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
    Returns an integer, representing the referenced row's ID.

        some_band.manager
        >>> 1

    Can also use it to perform joins:

        await Band.select(Band.name, Band.manager.name).run()

    To get a referenced row as an object:

        await Manager.objects().where(Manager.id == some_band.manager).run()

    Or use either of the following, which are just a proxy to the above:

        await some_band.get_related('manager').run()
        await some_band.get_related(Band.manager).run()

    To change the manager:

        some_band.manager = some_manager_id
        await some_band.save().run()

    """

    column_type = "INTEGER"

    def __init__(
        self,
        references: t.Union[t.Type[Table], str],
        on_delete: OnDelete = OnDelete.cascade,
        on_update: OnUpdate = OnUpdate.cascade,
        **kwargs,
    ) -> None:
        if isinstance(references, str):
            # if references != "self":
            #     raise ValueError(
            #         "String values for 'references' currently only supports "
            #         "'self', which is a reference to the current table."
            #     )
            pass

        kwargs.update(
            {
                "references": references,
                "on_delete": on_delete,
                "on_update": on_update,
            }
        )
        super().__init__(**kwargs)

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
