from __future__ import annotations
import asyncio
import importlib
import os
import sys
from types import ModuleType
import typing as t

from piccolo.conf.apps import AppConfig
from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.apps.migrations.auto.diffable_table import DiffableTable
from piccolo.apps.migrations.auto.schema_snapshot import SchemaSnapshot
from piccolo.apps.migrations.tables import Migration


class MigrationModule(ModuleType):
    @staticmethod
    async def forwards() -> None:
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

    def get_app_config(self, app_name: str) -> AppConfig:
        modules = self.get_app_modules()
        for module in modules:
            app_config = module.APP_CONFIG
            if app_config.app_name == app_name:
                return app_config
        raise ValueError(f"No app found with name {app_name}")

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

    def get_migration_managers(
        self,
        app_name: str,
        max_migration_id: t.Optional[str] = None,
        offset: int = 0,
    ) -> t.List[MigrationManager]:
        """
        :param max_migration_id:
            If set, only MigrationManagers up to and including the given
            migration ID will be returned.
        """
        migration_managers: t.List[MigrationManager] = []

        app_config = self.get_app_config(app_name=app_name)

        migrations_folder = app_config.migrations_folder_path

        migration_modules: t.Dict[
            str, MigrationModule
        ] = self.get_migration_modules(migrations_folder)

        for _, migration_module in migration_modules.items():
            response = asyncio.run(migration_module.forwards())
            if isinstance(response, MigrationManager):
                if max_migration_id:
                    if response.migration_id == max_migration_id:
                        break
                    else:
                        migration_managers.append(response)
                else:
                    migration_managers.append(response)

        if offset > 0:
            raise Exception(
                "Positive offset values aren't currently supported"
            )
        elif offset < 0:
            return migration_managers[0:offset]
        else:
            return migration_managers

    def get_table_from_snaphot(
        self,
        app_name: str,
        table_class_name: str,
        max_migration_id: t.Optional[str] = None,
        offset: int = 0,
    ) -> DiffableTable:
        """
        This will generate a SchemaSnapshot up to the given migration ID, and
        will return a DiffableTable class from that snapshot.
        """
        migration_managers = self.get_migration_managers(
            app_name=app_name, max_migration_id=max_migration_id, offset=offset
        )
        schema_snapshot = SchemaSnapshot(managers=migration_managers)

        return schema_snapshot.get_table_from_snapshot(
            table_class_name=table_class_name
        )
