import asyncio
import importlib
import os
import pprint
from types import ModuleType
import typing as t

import click

from piccolo.migrations.table import Migration
from piccolo.commands.migration.utils import (
    get_migration_modules,
    get_migration_ids,
)


ModuleList = t.List[ModuleType]


class ForwardsMigrationManager:
    def _create_migration_table(self) -> bool:
        """
        Creates the migration table in the database. Returns True/False
        depending on whether it was created or not.
        """
        if not Migration.table_exists().run_sync():
            Migration.create().run_sync()
            return True
        return False

    def deduplicate(self, config_modules: ModuleList) -> ModuleList:
        """
        Remove all duplicates - just leaving the first instance.
        """
        return list(dict([(c, None) for c in config_modules]).keys())

    def get_config_modules(self, migrations: t.List[str]) -> ModuleList:
        config_modules = []

        for config_module_path in migrations:
            try:
                config_module = importlib.import_module(config_module_path)
            except ImportError:
                raise Exception(f"Unable to import {config_module_path}")
            DEPENDENCIES = getattr(config_module, "DEPENDENCIES", [])
            dependency_config_modules = self.get_config_modules(DEPENDENCIES)
            config_modules.extend(dependency_config_modules + [config_module])

        return config_modules

    def run_migrations(self, config_modules: ModuleList) -> None:
        already_ran = Migration.get_migrations_which_ran()
        print(f"Already ran:\n{already_ran}\n")

        for config_module in config_modules:
            migrations_folder = os.path.dirname(config_module.__file__)

            migration_modules = get_migration_modules(migrations_folder)
            ids = get_migration_ids(migration_modules)
            print(f"Migration ids = {ids}")

            app_name = getattr(config_module, "NAME", "")

            havent_run = sorted(set(ids) - set(already_ran))
            for _id in havent_run:
                migration_module = migration_modules[_id]
                asyncio.run(migration_module.forwards())

                print(f"Ran {_id}")
                Migration.insert().add(
                    Migration(name=_id, app_name=app_name)
                ).run_sync()

    def run(self):
        print("Running migrations ...")
        self._create_migration_table()

        try:
            from piccolo_conf import MIGRATIONS
        except ImportError:
            raise Exception(
                "Unable to import MIGRATIONS from piccolo_conf - make sure "
                "it's in your path."
            )

        config_modules = self.get_config_modules(MIGRATIONS)

        # Now deduplicate any dependencies
        config_modules = self.deduplicate(config_modules)

        print("Config Modules:")
        pprint.pprint(config_modules)
        print("\n")

        self.run_migrations(config_modules)


@click.command()
def forwards():
    """
    Runs any migrations which haven't been run yet, or up to a specific
    migration.
    """
    manager = ForwardsMigrationManager()
    manager.run()
