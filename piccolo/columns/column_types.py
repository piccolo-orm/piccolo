import copy
from datetime import datetime
import typing as t

from piccolo.columns.base import Column
from piccolo.querystring import Unquoted

if t.TYPE_CHECKING:
    import table  # noqa
    from piccolo.custom_types import Datetime  # noqa


class Varchar(Column):

    value_type = str

    def __init__(self, length: int = 255, default: str = None,
                 **kwargs) -> None:
        self.length = length
        self.default = default
        super().__init__(**kwargs)


class Integer(Column):

    def __init__(self, default: int = None, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class Serial(Column):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


DEFAULT = Unquoted('DEFAULT')
NULL = Unquoted('null')


class PrimaryKey(Column):

    @property
    def column_type(self):
        engine_type = self._table.Meta.db.engine_type
        if engine_type == 'postgres':
            return 'SERIAL'
        elif engine_type == 'sqlite':
            return 'INTEGER'
        raise Exception('Unrecognized engine type')

    def default(self):
        engine_type = self._table.Meta.db.engine_type
        if engine_type == 'postgres':
            return DEFAULT
        elif engine_type == 'sqlite':
            return NULL
        raise Exception('Unrecognized engine type')

    def __init__(self, **kwargs) -> None:
        kwargs.update({
            'primary': True,
            'key': True
        })
        super().__init__(**kwargs)


class Timestamp(Column):

    value_type = datetime

    def __init__(self, default: 'Datetime' = None, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class Boolean(Column):

    value_type = bool

    def __init__(self, default: bool = False, **kwargs) -> None:
        self.default = default
        super().__init__(**kwargs)


class ForeignKey(Integer):
    """
    Returns an integer, representing the referenced row's ID.

        some_band.manager
        >>> 1

    Can also use it to perform joins:

        Band.select.columns(Band.manager.name)

    To get a referenced row as an object:

        User.object.where(User.id == some_band.manager)

    Or use this, which is just a proxy to the above:

        some_band.related_object('manager')

    To change the manager:

        some_band.manager = some_manager_id
        some_band.save

    Or:
        some_band.set_related_object('manager', some_manager)

    """

    column_type = 'INTEGER'

    def __getattribute__(self, name):
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

        foreignkey_class = object.__getattribute__(self, '__class__')

        if type(value) == foreignkey_class:  # i.e. a ForeignKey
            new_column = copy.deepcopy(value)
            new_column.call_chain = copy.copy(self.call_chain)
            new_column.call_chain.append(self)

            # We have to set limits to the call chain because Table 1 can
            # reference Table 2, which references Table 1, creating an endless
            # loop. For now an arbitrary limit is set of 10 levels deep.
            # When querying a call chain more than 10 levels deep, an error
            # will be raised. Often there are more effective ways of
            # structuring a query than joining so many tables anyway.
            if len(new_column.call_chain) > 10:
                raise Exception('Call chain too long!')

            for proxy_column in self.proxy_columns:
                try:
                    delattr(new_column, proxy_column._name)
                except Exception:
                    pass

            for column in value.references.Meta.columns:
                _column = copy.deepcopy(column)
                _column.call_chain = copy.copy(new_column.call_chain)
                _column.call_chain.append(new_column)
                if _column._name == 'id':
                    continue
                setattr(new_column, _column._name, _column)
                self.proxy_columns.append(_column)

            return new_column
        elif issubclass(type(value), Column):
            new_column = copy.deepcopy(value)
            new_column.call_chain = copy.copy(self.call_chain)
            new_column.call_chain.append(self)
            return new_column
        else:
            return value

    def __init__(self, references: t.Type['table.Table'], **kwargs) -> None:
        super().__init__(**kwargs)
        self.references = references
        self.proxy_columns: t.List[Column] = []

        # Allow columns on the referenced table to be accessed via auto
        # completion.
        for column in references.Meta.columns:
            _column = copy.deepcopy(column)
            setattr(self, column._name, _column)
            self.proxy_columns.append(_column)
