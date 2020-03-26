from __future__ import annotations
import importlib
import os
import sys
from types import ModuleType
import typing as t

from piccolo.conf.apps import AppConfig
from piccolo.migrations.tables import Migration


class MigrationModule(ModuleType):
    @staticmethod
    async def forwards() -> None:
        pass

    @staticmethod
    async def backwards() -> None:
        pass


class PiccoloAppModule(ModuleType):
    APP_CONFIG: AppConfig


class BaseMigrationManager:
    def create_migration_table(self) -> bool:
        """
        Creates the migration table in the database. Returns True/False
        depending on whether it was created or not.
        """
        if not Migration.table_exists().run_sync():
            Migration.create_table().run_sync()
            return True
        return False

    def _deduplicate(
        self, config_modules: t.List[PiccoloAppModule]
    ) -> t.List[PiccoloAppModule]:
        """
        Remove all duplicates - just leaving the first instance.
        """
        # Deduplicate, but preserve order - which is why set() isn't used.
        return list(dict([(c, None) for c in config_modules]).keys())

    def _import_app_modules(
        self, config_module_paths: t.List[str]
    ) -> t.List[PiccoloAppModule]:
        """
        Import all piccolo_app.py modules, and all dependencies.
        """
        config_modules = []

        for config_module_path in config_module_paths:
            try:
                config_module = t.cast(
                    PiccoloAppModule,
                    importlib.import_module(config_module_path),
                )
            except ImportError:
                raise Exception(f"Unable to import {config_module_path}")
            app_config: AppConfig = getattr(config_module, "APP_CONFIG")
            dependency_config_modules = self._import_app_modules(
                app_config.migration_dependencies
            )
            config_modules.extend(dependency_config_modules + [config_module])

        return config_modules

    def get_app_modules(self) -> t.List[PiccoloAppModule]:
        try:
            from piccolo_conf import APP_REGISTRY
        except ImportError:
            raise Exception(
                "Unable to import APP_REGISTRY from piccolo_conf - make sure "
                "it's in your path."
            )

        app_modules = self._import_app_modules(APP_REGISTRY.apps)

        # Now deduplicate any dependencies
        app_modules = self._deduplicate(app_modules)

        return app_modules

    def get_migration_modules(
        self, folder_path: str
    ) -> t.Dict[str, MigrationModule]:
        """
        Import the migration modules and store them in a dictionary.
        """
        migration_modules = {}

        sys.path.insert(0, folder_path)

        folder_contents = os.listdir(folder_path)
        excluded = ("__init__.py", "__pycache__")
        migration_names = [
            i.split(".py")[0]
            for i in folder_contents
            if ((i not in excluded) and (not i.startswith(".")))
        ]

        modules: t.List[MigrationModule] = [
            t.cast(MigrationModule, importlib.import_module(name))
            for name in migration_names
        ]
        for m in modules:
            _id = getattr(m, "ID", None)
            if _id:
                migration_modules[_id] = m

        return migration_modules

    def get_migration_ids(
        self, migration_module_dict: t.Dict[str, MigrationModule]
    ) -> t.List[str]:
        return sorted(list(migration_module_dict.keys()))
