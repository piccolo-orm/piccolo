import asyncio
import os
import sys

import click

from piccolo.migrations.table import Migration
from piccolo.commands.migration.utils import (
    get_migration_modules,
    get_migration_ids,
    ModuleDict,
)


class ForwardsMigrationManager:
    def __init__(self):
        self.migrations_folder = os.path.join(os.getcwd(), "migrations")
        self.migration_modules: ModuleDict = {}

    def _create_migration_table(self) -> bool:
        """
        Creates the migration table in the database. Returns True/False
        depending on whether it was created or not.
        """
        if not Migration.table_exists().run_sync():
            Migration.create().run_sync()
            return True
        return False

    def run(self):
        print("Running migrations ...")
        sys.path.insert(0, os.getcwd())

        self._create_migration_table()

        already_ran = Migration.get_migrations_which_ran()
        print(f"Already ran = {already_ran}")

        self.migration_modules = get_migration_modules(
            self.migrations_folder, recursive=True
        )
        ids = get_migration_ids(self.migration_modules)
        print(f"Migration ids = {ids}")

        havent_run = sorted(set(ids) - set(already_ran))
        for _id in havent_run:
            migration_module = self.migration_modules[_id]
            asyncio.run(migration_module.forwards())

            print(f"Ran {_id}")
            Migration.insert().add(
                Migration(name=_id, app_name=migration_module.app_name)
            ).run_sync()


@click.command()
def forwards():
    """
    Runs any migrations which haven't been run yet, or up to a specific
    migration.
    """
    manager = ForwardsMigrationManager()
    manager.run()
