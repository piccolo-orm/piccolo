from __future__ import annotations
from dataclasses import dataclass, field
from importlib import import_module
import typing as t

from piccolo.table import Table


def table_finder(
    modules: t.Sequence[str],
    include_tags: t.Sequence[str] = ["__all__"],
    exclude_tags: t.Sequence[str] = [],
) -> t.List[t.Type[Table]]:
    """
    Rather than explicitly importing and registering table classes with the
    AppConfig, ``table_finder`` can be used instead. It imports any ``Table``
    subclasses in the given modules. Tags can be used to limit which ``Table``
    subclasses are imported.

    :param modules:
        The module paths to check for ``Table`` subclasses. For example,
        ['blog.tables']. The path should be from the root of your project,
        not a relative path.
    :param include_tags:
        If the ``Table`` subclass has one of these tags, it will be
        imported. The special tag '__all__' will import all ``Table``
        subclasses found.
    :param exclude_tags:
        If the ``Table`` subclass has any of these tags, it won't be
        imported. `exclude_tags` overrides `include_tags`.

    """
    table_subclasses: t.List[t.Type[Table]] = []

    for module_path in modules:
        try:
            module = import_module(module_path)
        except ImportError as exception:
            print(f"Unable to import {module_path}")
            raise exception

        object_names = [i for i in dir(module) if not i.startswith("_")]

        for object_name in object_names:
            _object = getattr(module, object_name)
            if issubclass(_object, Table) and _object is not Table:
                table: Table = _object
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
class AppConfig:
    app_name: str
    migrations_folder_path: str
    table_classes: t.List[t.Type[Table]] = field(default_factory=list)
    migration_dependencies: t.List[str] = field(default_factory=list)
    commands: t.List[t.Callable] = field(default_factory=list)

    def register_table(self, table_class: t.Type[Table]):
        self.table_classes.append(table_class)
        return table_class


@dataclass
class AppRegistry:
    apps: t.List[str] = field(default_factory=list)

    def __post_init__(self):
        self.app_configs: t.Dict[str, AppConfig] = {}
        for app in self.apps:
            app_conf_module = import_module(app)
            app_config: AppConfig = getattr(app_conf_module, "APP_CONFIG")
            self.app_configs[app_config.app_name] = app_config

    def get_app_config(self, app_name: str) -> t.Optional[AppConfig]:
        return self.app_configs.get(app_name)

    def get_table_classes(self, app_name: str):
        """
        Returns each Table subclass defined in the given app.
        """
        app_config = self.get_app_config(app_name=app_name)
        if not app_config:
            raise ValueError(f"Unrecognised app_name: {app_name}")
        return app_config.table_classes
