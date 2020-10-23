from __future__ import annotations
import asyncio
import importlib
import os
import sys
import typing as t

from piccolo.conf.apps import (
    MigrationModule,
    Finder,
)
from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.apps.migrations.auto.diffable_table import DiffableTable
from piccolo.apps.migrations.auto.schema_snapshot import SchemaSnapshot
from piccolo.apps.migrations.tables import Migration


class BaseMigrationManager(Finder):
    def create_migration_table(self) -> bool:
        """
        Creates the migration table in the database. Returns True/False
        depending on whether it was created or not.
        """
        if not Migration.table_exists().run_sync():
            Migration.create_table().run_sync()
            return True
        return False

    def get_migration_modules(
        self, folder_path: str
    ) -> t.Dict[str, MigrationModule]:
        """
        Import the migration modules and store them in a dictionary.
        """
        migration_modules = {}

        sys.path.insert(0, folder_path)

        folder_contents = os.listdir(folder_path)
        excluded = ("__init__.py",)
        migration_names = [
            i.split(".py")[0]
            for i in folder_contents
            if ((i not in excluded) and i.endswith(".py"))
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
        """
        Returns a list of migration IDs, from the Python migration files.
        """
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
