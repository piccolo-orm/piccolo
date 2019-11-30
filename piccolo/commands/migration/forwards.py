import asyncio
import os
import pprint

import click

from piccolo.migrations.tables import Migration
from .base import BaseMigrationManager, ModuleList


class ForwardsMigrationManager(BaseMigrationManager):
    def run_migrations(self, config_modules: ModuleList) -> None:
        already_ran = Migration.get_migrations_which_ran()
        print(f"Already ran:\n{already_ran}\n")

        for config_module in config_modules:
            migrations_folder = os.path.dirname(config_module.__file__)

            migration_modules = self.get_migration_modules(migrations_folder)
            ids = self.get_migration_ids(migration_modules)
            print(f"Migration ids = {ids}")

            app_name = self.get_app_name(config_module)

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
        self.create_migration_table()

        config_modules = self.get_config_modules()

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
