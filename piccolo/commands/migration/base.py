from __future__ import annotations
import importlib
import os
import sys
from types import ModuleType
import typing as t

from piccolo.migrations.tables import Migration


class MigrationModule(ModuleType):
    @staticmethod
    async def forwards() -> None:
        pass

    @staticmethod
    async def backwards() -> None:
        pass


class ConfigModule(ModuleType):
    NAME: str
    DEPENDENCIES: t.List[str]


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
        self, config_modules: t.List[ConfigModule]
    ) -> t.List[ConfigModule]:
        """
        Remove all duplicates - just leaving the first instance.
        """
        return list(dict([(c, None) for c in config_modules]).keys())

    def import_config_modules(
        self, migrations: t.List[str]
    ) -> t.List[ConfigModule]:
        """
        Import all config modules, and all dependencies.
        """
        config_modules = []

        for config_module_path in migrations:
            try:
                config_module = t.cast(
                    ConfigModule, importlib.import_module(config_module_path)
                )
            except ImportError:
                raise Exception(f"Unable to import {config_module_path}")
            DEPENDENCIES = getattr(config_module, "DEPENDENCIES", [])
            dependency_config_modules = self.import_config_modules(
                DEPENDENCIES
            )
            config_modules.extend(dependency_config_modules + [config_module])

        return config_modules

    def get_config_modules(self) -> t.List[ConfigModule]:
        try:
            from piccolo_conf import MIGRATIONS
        except ImportError:
            raise Exception(
                "Unable to import MIGRATIONS from piccolo_conf - make sure "
                "it's in your path."
            )

        config_modules = self.import_config_modules(MIGRATIONS)

        # Now deduplicate any dependencies
        config_modules = self._deduplicate(config_modules)

        return config_modules

    def get_migration_modules(
        self, folder_path: str
    ) -> t.Dict[str, MigrationModule]:
        """
        Import the migration modules and store them in a dictionary.
        """
        migration_modules = {}

        sys.path.insert(0, folder_path)

        folder_contents = os.listdir(folder_path)
        excluded = ("__init__.py", "__pycache__", "config.py")
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

    def get_app_name(self, config_module: ConfigModule) -> str:
        app_name = getattr(config_module, "NAME", "").strip()
        return app_name
