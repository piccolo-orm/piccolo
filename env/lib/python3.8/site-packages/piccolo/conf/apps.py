from __future__ import annotations

import functools
import inspect
import itertools
import os
import pathlib
import traceback
import typing as t
from dataclasses import dataclass, field
from importlib import import_module
from types import ModuleType

from piccolo.engine.base import Engine
from piccolo.table import Table
from piccolo.utils.warnings import Level, colored_warning


class MigrationModule(ModuleType):
    ID: str
    VERSION: str
    DESCRIPTION: str

    @staticmethod
    async def forwards() -> None:
        pass


class PiccoloAppModule(ModuleType):
    APP_CONFIG: AppConfig


def table_finder(
    modules: t.Sequence[str],
    include_tags: t.Sequence[str] = None,
    exclude_tags: t.Sequence[str] = None,
    exclude_imported: bool = False,
) -> t.List[t.Type[Table]]:
    """
    Rather than explicitly importing and registering table classes with the
    ``AppConfig``, ``table_finder`` can be used instead. It imports any ``Table``
    subclasses in the given modules. Tags can be used to limit which ``Table``
    subclasses are imported.

    :param modules:
        The module paths to check for ``Table`` subclasses. For example,
        ``['blog.tables']``. The path should be from the root of your project,
        not a relative path.
    :param include_tags:
        If the ``Table`` subclass has one of these tags, it will be
        imported. The special tag ``'__all__'`` will import all ``Table``
        subclasses found.
    :param exclude_tags:
        If the ``Table`` subclass has any of these tags, it won't be
        imported. ``exclude_tags`` overrides ``include_tags``.
    :param exclude_imported:
        If ``True``, only ``Table`` subclasses defined within the module are
        used. Any ``Table`` subclasses imported by that module from other
        modules are ignored. For example:

        .. code-block:: python

            from piccolo.table import Table
            from piccolo.column import Varchar, ForeignKey
            from piccolo.apps.user.tables import BaseUser # excluded

            class Task(Table): # included
                title = Varchar()
                creator = ForeignKey(BaseUser)

    """  # noqa: E501
    if include_tags is None:
        include_tags = ["__all__"]
    if exclude_tags is None:
        exclude_tags = []
    if isinstance(modules, str):
        # Guard against the user just entering a string, for example
        # 'blog.tables', instead of ['blog.tables'].
        modules = [modules]

    table_subclasses: t.List[t.Type[Table]] = []

    for module_path in modules:
        try:
            module = import_module(module_path)
        except ImportError as exception:
            print(f"Unable to import {module_path}")
            raise exception from exception

        object_names = [i for i in dir(module) if not i.startswith("_")]

        for object_name in object_names:
            _object = getattr(module, object_name)
            if (
                inspect.isclass(_object)
                and issubclass(_object, Table)
                and _object is not Table
            ):
                table: Table = _object  # type: ignore

                if exclude_imported and table.__module__ != module_path:
                    continue

                if exclude_tags and set(table._meta.tags).intersection(
                    set(exclude_tags)
                ):
                    continue
                elif "__all__" in include_tags:
                    table_subclasses.append(_object)
                elif set(table._meta.tags).intersection(set(include_tags)):
                    table_subclasses.append(_object)

    return table_subclasses


@dataclass
class Command:
    callable: t.Callable
    aliases: t.List[str] = field(default_factory=list)


@dataclass
class AppConfig:
    """
    Each app needs an AppConfig, which is defined in piccolo_app.py.

    :param app_name:
        The name of the app, for example ``'article'``.
    :param migrations_folder_path:
        The path of the folder containing this app's migration files.
    :param table_classes:
        By registering table classes, Piccolo's auto migrations can detect
        changes to tables.
    :param migration_dependencies:
        A list of Piccolo apps whose migrations this app depends on. For
        example: ``['piccolo.apps.user.piccolo_conf']``. The migrations for
        those apps will be run before the migrations for this app.
    :param commands:
        A list of functions and coroutines, which are then registered with
        the Piccolo CLI. For example, with a Piccolo app called ``'article'``,
        and a command called ``new``, it can be called on the command line
        using ``piccolo article new``.

    """

    app_name: str
    migrations_folder_path: str
    table_classes: t.List[t.Type[Table]] = field(default_factory=list)
    migration_dependencies: t.List[str] = field(default_factory=list)
    commands: t.List[t.Union[t.Callable, Command]] = field(
        default_factory=list
    )

    def __post_init__(self):
        self.commands = [
            i if isinstance(i, Command) else Command(i) for i in self.commands
        ]

        if isinstance(self.migrations_folder_path, pathlib.Path):
            self.migrations_folder_path = str(self.migrations_folder_path)

    def register_table(self, table_class: t.Type[Table]):
        self.table_classes.append(table_class)
        return table_class

    @property
    def migration_dependency_app_configs(self) -> t.List[AppConfig]:
        """
        Get all of the AppConfig instances from this app's migration
        dependencies.
        """
        modules: t.List[PiccoloAppModule] = [
            t.cast(PiccoloAppModule, import_module(module_path))
            for module_path in self.migration_dependencies
        ]
        return [i.APP_CONFIG for i in modules]

    def get_table_with_name(self, table_class_name: str) -> t.Type[Table]:
        """
        Returns a Table subclass with the given name from this app, if it
        exists. Otherwise raises a ValueError.
        """
        filtered = [
            table_class
            for table_class in self.table_classes
            if table_class.__name__ == table_class_name
        ]
        if not filtered:
            raise ValueError(
                f"No table with class name {table_class_name} exists."
            )
        return filtered[0]


class AppRegistry:
    """
    Records all of the Piccolo apps in your project. Kept in
    ``piccolo_conf.py``.

    :param apps:
        A list of paths to Piccolo apps, e.g. ``['blog.piccolo_app']``.

    """

    def __init__(self, apps: t.List[str] = None):
        self.apps = apps or []
        self.app_configs: t.Dict[str, AppConfig] = {}
        app_names = []

        for app in self.apps:
            try:
                app_conf_module = import_module(app)
                app_config: AppConfig = getattr(app_conf_module, "APP_CONFIG")
            except (ImportError, AttributeError) as e:
                if app.endswith(".piccolo_app"):
                    raise e from e
                app += ".piccolo_app"
                app_conf_module = import_module(app)
                app_config = getattr(app_conf_module, "APP_CONFIG")
                colored_warning(
                    f"App {app[:-12]} should end with `.piccolo_app`",
                    level=Level.medium,
                )

            self.app_configs[app_config.app_name] = app_config
            app_names.append(app_config.app_name)

        self._validate_app_names(app_names)

    @staticmethod
    def _validate_app_names(app_names: t.List[str]):
        """
        Raise a ValueError if an app_name is repeated.
        """
        app_names.sort()
        grouped = itertools.groupby(app_names)
        for key, value in grouped:
            count = len(list(value))
            if count > 1:
                raise ValueError(
                    f"There are {count} apps with the name `{key}`. This can "
                    "cause unexpected behavior. Make sure each app has a "
                    "unique name, and you haven't registered the same app "
                    "multiple times."
                )

    def get_app_config(self, app_name: str) -> t.Optional[AppConfig]:
        return self.app_configs.get(app_name)

    def get_table_classes(self, app_name: str) -> t.List[t.Type[Table]]:
        """
        Returns each Table subclass defined in the given app if it exists.
        Otherwise raises a ValueError.

        :raises ValueError:
            If an AppConfig can't be found for the given app_name.

        """
        app_config = self.get_app_config(app_name=app_name)
        if not app_config:
            raise ValueError(f"Unrecognised app_name: {app_name}")
        return app_config.table_classes

    def get_table_with_name(
        self, app_name: str, table_class_name: str
    ) -> t.Optional[t.Type[Table]]:
        """
        Returns a Table subclass registered with the given app if it exists.
        Otherwise raises a ValueError.
        """
        app_config = self.get_app_config(app_name=app_name)
        if app_config is None:
            raise ValueError(f"Can't find an app_config for {app_name}")
        else:
            return app_config.get_table_with_name(
                table_class_name=table_class_name
            )


class PiccoloConfModule(ModuleType):
    DB: Engine
    APP_REGISTRY: AppRegistry


DEFAULT_MODULE_NAME = "piccolo_conf"
ENVIRONMENT_VARIABLE = "PICCOLO_CONF"
ENGINE_VAR = "DB"


class Finder:
    """
    Contains useful methods for locating and loading apps within your project,
    and tables within apps.
    """

    def __init__(self, diagnose: bool = False):
        """
        :param diagnose:
            If True, when trying to import piccolo_conf, a traceback will be
            printed out if an error occurs.

        """
        self.diagnose = diagnose

    def _deduplicate(
        self, config_modules: t.List[PiccoloAppModule]
    ) -> t.List[PiccoloAppModule]:
        """
        Remove all duplicates - just leaving the first instance.
        """
        # Deduplicate, but preserve order - which is why set() isn't used.
        return list({c: None for c in config_modules}.keys())

    def _import_app_modules(
        self, config_module_paths: t.List[str]
    ) -> t.List[PiccoloAppModule]:
        """
        Import all piccolo_app.py modules within your apps, and all
        dependencies.
        """
        config_modules = []

        for config_module_path in config_module_paths:
            try:
                config_module = t.cast(
                    PiccoloAppModule, import_module(config_module_path)
                )
            except ImportError as e:
                raise Exception(
                    f"Unable to import {config_module_path}"
                ) from e
            app_config: AppConfig = getattr(config_module, "APP_CONFIG")
            dependency_config_modules = self._import_app_modules(
                app_config.migration_dependencies
            )
            config_modules.extend(dependency_config_modules + [config_module])

        return config_modules

    def get_piccolo_conf_module(
        self, module_name: t.Optional[str] = None
    ) -> t.Optional[PiccoloConfModule]:
        """
        Searches the path for a 'piccolo_conf.py' module to import. The
        location searched can be overriden by:

        * Explicitly passing a module name into this method.
        * Setting the PICCOLO_CONF environment variable.

        An example override is 'my_folder.piccolo_conf'.

        """
        env_module_name = os.environ.get(ENVIRONMENT_VARIABLE, None)

        if not module_name and env_module_name:
            module_name = env_module_name

        if not module_name:
            module_name = DEFAULT_MODULE_NAME

        try:
            module = t.cast(PiccoloConfModule, import_module(module_name))
        except ModuleNotFoundError as exc:
            if self.diagnose:
                colored_warning(
                    (
                        f"{module_name} either doesn't exist or the import "
                        "failed. Traceback:"
                    ),
                    level=Level.high,
                )
                print(traceback.format_exc())

            if str(exc) == "No module named 'asyncpg'":
                raise ModuleNotFoundError(
                    "PostgreSQL driver not found. "
                    "Try running `pip install 'piccolo[postgres]'`"
                ) from exc
            elif str(exc) == "No module named 'aiosqlite'":
                raise ModuleNotFoundError(
                    "SQLite driver not found. "
                    "Try running `pip install 'piccolo[sqlite]'`"
                ) from exc
            else:
                raise exc from exc
        else:
            return module

    def get_app_registry(self) -> AppRegistry:
        """
        Returns the ``AppRegistry`` instance within piccolo_conf.
        """
        piccolo_conf_module = self.get_piccolo_conf_module()
        return getattr(piccolo_conf_module, "APP_REGISTRY")

    def get_engine(
        self, module_name: t.Optional[str] = None
    ) -> t.Optional[Engine]:
        piccolo_conf = self.get_piccolo_conf_module(module_name=module_name)
        engine: t.Optional[Engine] = getattr(piccolo_conf, ENGINE_VAR, None)

        if not engine:
            colored_warning(
                f"{module_name} doesn't define a {ENGINE_VAR} variable.",
                level=Level.high,
            )
        elif not isinstance(engine, Engine):
            colored_warning(
                f"{module_name} contains a {ENGINE_VAR} variable of the "
                "wrong type - it should be an Engine subclass.",
                level=Level.high,
            )

        return engine

    def get_app_modules(self) -> t.List[PiccoloAppModule]:
        """
        Returns the ``piccolo_app.py`` modules for each registered Piccolo app
        in your project.
        """
        app_registry = self.get_app_registry()
        app_modules = self._import_app_modules(app_registry.apps)

        # Now deduplicate any dependencies
        app_modules = self._deduplicate(app_modules)

        return app_modules

    def get_app_names(self, sort: bool = True) -> t.List[str]:
        """
        Return all of the app names.

        :param sort:
            If True, sorts the app names using the migration dependencies, so
            dependencies are before dependents in the list.

        """
        modules = self.get_app_modules()
        configs: t.List[AppConfig] = [module.APP_CONFIG for module in modules]

        if not sort:
            return [i.app_name for i in configs]

        def sort_app_configs(app_config_1: AppConfig, app_config_2: AppConfig):
            return (
                app_config_1 in app_config_2.migration_dependency_app_configs
            )

        sorted_configs = sorted(
            configs, key=functools.cmp_to_key(sort_app_configs)
        )
        return [i.app_name for i in sorted_configs]

    def get_sorted_app_names(self) -> t.List[str]:
        """
        Just here for backwards compatibility.
        """
        return self.get_app_names(sort=True)

    def get_app_config(self, app_name: str) -> AppConfig:
        """
        Returns an ``AppConfig`` for the given app name.
        """
        modules = self.get_app_modules()
        for module in modules:
            app_config = module.APP_CONFIG
            if app_config.app_name == app_name:
                return app_config
        raise ValueError(f"No app found with name {app_name}")

    def get_table_with_name(
        self, app_name: str, table_class_name: str
    ) -> t.Type[Table]:
        """
        Returns a ``Table`` class registered with the given app if it exists.
        Otherwise it raises an ``ValueError``.
        """
        app_config = self.get_app_config(app_name=app_name)
        return app_config.get_table_with_name(
            table_class_name=table_class_name
        )

    def get_table_classes(
        self,
        include_apps: t.Optional[t.List[str]] = None,
        exclude_apps: t.Optional[t.List[str]] = None,
    ) -> t.List[t.Type[Table]]:
        """
        Returns all ``Table`` classes registered with the given apps. If
        ``app_names`` is ``None``, then ``Table`` classes will be returned
        for all apps.
        """
        if include_apps and exclude_apps:
            raise ValueError("Only specify `include_apps` or `exclude_apps`.")

        if include_apps:
            app_names = include_apps
        else:
            app_names = self.get_app_names()
            if exclude_apps:
                app_names = [i for i in app_names if i not in exclude_apps]

        tables: t.List[t.Type[Table]] = []

        for app_name in app_names:
            app_config = self.get_app_config(app_name=app_name)
            tables.extend(app_config.table_classes)

        return tables
