from __future__ import annotations
from dataclasses import dataclass, field
from importlib import import_module
import typing as t

if t.TYPE_CHECKING:
    from piccolo.table import Table


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
