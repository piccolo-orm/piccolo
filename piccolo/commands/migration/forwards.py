import asyncio
import importlib
import importlib.util
import os
import sys
import typing as t
from types import ModuleType

import click

from piccolo.migrations.table import Migration


class ForwardsMigrationManager:
    def __init__(self, migration_name: str):
        self.migrations_folder = os.path.join(os.getcwd(), "migrations")
        self.migration_modules: t.Dict[str, ModuleType] = {}
        self.migration_name = migration_name

    def modify_path(self):
        sys.path.insert(0, self.migrations_folder)

    def _get_migration_ids(self) -> t.List[str]:
        return list(self.migration_modules.keys())

    def _get_migration_modules(self) -> None:
        """
        Import the migration modules and store them in a dictionary.
        """
        folder_contents = os.listdir(self.migrations_folder)
        excluded = ("__init__.py", "__pycache__")
        migration_names = [
            i.split(".py")[0]
            for i in folder_contents
            if ((i not in excluded) and (not i.startswith(".")))
        ]
        modules = [importlib.import_module(name) for name in migration_names]
        for m in modules:
            _id = getattr(m, "ID", None)
            if _id:
                self.migration_modules[_id] = m

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

        self._get_migration_modules()
        ids = self._get_migration_ids()
        print(f"Migration ids = {ids}")

        for _id in set(ids) - set(already_ran):
            asyncio.run(self.migration_modules[_id].forwards())

            print(f"Ran {_id}")
            Migration.insert().add(Migration(name=_id)).run_sync()


@click.command()
def forwards():
    """
    Runs any migrations which haven't been run yet, or up to a specific
    migration.
    """
    manager = ForwardsMigrationManager()
    manager.run()
