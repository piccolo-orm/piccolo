import asyncio
import importlib
import importlib.util
import os
import sys
import typing as t
from types import ModuleType

import click

from piccolo.migrations.table import Migration


class BackwardsMigrationManager:
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

    def run(self):
        self.modify_path()
        self._get_migration_modules()

        migration_ids = self._get_migration_ids()

        if self.migration_name not in migration_ids:
            print(
                f"Unrecognized migration name - must be one of {migration_ids}"
            )

        _continue = input(
            "About to undo the migrations - press y to continue."
        )
        if _continue == "y":
            print("Undoing migrations")

            _sorted = sorted(list(self.migration_modules.keys()))
            _sorted = _sorted[_sorted.index(self.migration_name)]
            _sorted.reverse()

            already_ran = Migration.get_migrations_which_ran()

            for s in _sorted:
                if s not in already_ran:
                    print(f"Migration {s} hasn't run yet, can't undo!")
                    sys.exit(1)

                print(self.migration_name)
                asyncio.run(
                    self.migration_modules[s].backwards()
                )  # type: ignore

                Migration.delete().where(Migration.name == s).run_sync()
        else:
            print("Not proceeding.")


@click.command()
@click.argument("migration_name")
def backwards(migration_name: str):
    """
    Undo migrations up to a specific migrations.

    - make sure the migration name is valid
    - work out which to undo, and in which order
    - ask for confirmation
    - apply the undo operations one by one
    """
    manager = BackwardsMigrationManager(migration_name=migration_name)
    manager.run()
