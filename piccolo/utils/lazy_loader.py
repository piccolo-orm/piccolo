# https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/util/lazy_loader.py
from __future__ import absolute_import, division, print_function

import importlib
import types
import typing as t


class LazyLoader(types.ModuleType):
    """
    Lazily import a module.

    `PostgresEngine` and `SQLiteEngine` are example use cases.
    """

    def __init__(self, local_name, parent_module_globals, name):
        self._local_name = local_name
        self._parent_module_globals = parent_module_globals

        super().__init__(name)

    def _load(self) -> types.ModuleType:
        try:
            # Import the target module and
            # insert it into the parent's namespace
            module = importlib.import_module(self.__name__)
            self._parent_module_globals[self._local_name] = module

            # Update this object's dict so that
            # if someone keeps a reference to the
            #   LazyLoader, lookups are efficient
            #  (__getattr__ is only called on lookups that fail).
            self.__dict__.update(module.__dict__)

            return module

        except ModuleNotFoundError as exc:
            if str(exc) == "No module named 'asyncpg'":
                raise ModuleNotFoundError(
                    "PostgreSQL driver not found. "
                    "Try running `pip install 'piccolo[postgres]'`"
                )
            elif str(exc) == "No module named 'aiosqlite'":
                raise ModuleNotFoundError(
                    "SQLite driver not found. "
                    "Try running `pip install 'piccolo[sqlite]'`"
                )
            else:
                raise exc

    def __getattr__(self, item) -> t.Any:
        module = self._load()
        return getattr(module, item)

    def __dir__(self) -> t.List[str]:
        module = self._load()
        return dir(module)
