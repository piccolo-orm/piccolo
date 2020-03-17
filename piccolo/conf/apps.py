from dataclasses import dataclass
from importlib import import_module
import typing as t


@dataclass
class AppConfig:
    apps = t.List[str]

    def __post_init__(self):
        self.modules = {}
        for app in self.apps:
            app_conf_module = import_module(app)
            app_name = getattr(app_conf_module, "APP_NAME")
            self.modules[app_name] = app_conf_module

    def get_module(self, app_name: str):
        return self.modules.get(app_name)

    def get_tables_module(self, app_name: str):
        """
        Each app specifies a tables module which contains all Table subclasses.
        """
        pass

    def get_table_classes(self, app_name: str):
        """
        Returns each Table subclass defined in the given app.
        """
        tables_module = self.get_tables_module(app_name=app_name)
