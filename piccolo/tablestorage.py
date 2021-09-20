import typing as t

from piccolo.columns import Column
from piccolo.table import Table


class Immutable(object):
    def _immutable(self, *arg, **kw) -> TypeError:
        raise TypeError("%s object is immutable" % self.__class__.__name__)

    __delitem__ = __setitem__ = __setattr__ = _immutable


class ImmutableDict(Immutable, dict):
    """A dictionary that is not publicly mutable."""

    clear = pop = popitem = setdefault = update = Immutable._immutable

    def __new__(cls, *args):
        new = dict.__new__(cls)
        return new

    def copy(self):
        raise NotImplementedError(
            "an immutabledict shouldn't need to be copied.  use dict(d) "
            "if you need a mutable dictionary."
        )

    def __reduce__(self):
        return ImmutableDict, (dict(self),)

    def _insert_item(self, key, value) -> None:
        """
        insert an item into the dictionary directly.
        """
        dict.__setitem__(self, key, value)

    def _delete_item(self, key) -> None:
        """
        Delete an item from dictionary directly.
        """
        dict.__delitem__(self, key)

    def __repr__(self):
        return f"ImmutableDict({dict.__repr__(self)})"


class Singleton(type):
    """
     A metaclass that creates a Singleton base class when called.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class TableStorage(metaclass=Singleton):
    """
    A singleton object to store reflected tables
    """

    def __init__(self):
        self.tables = ImmutableDict()

    @staticmethod
    def _create_table(name, columns: t.Dict[str, Column], BaseClass=Table) -> type:
        """
        A factory for generating dynamic Table classes
        """

        for key, value in columns.items():
            if not isinstance(value, Column):
                raise TypeError(f"Argument {key} must be a Column object.")

        newtable = type(name, (BaseClass,), columns)
        return newtable
