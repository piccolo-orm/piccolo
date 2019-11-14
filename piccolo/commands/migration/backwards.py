import asyncio
import os
import sys
import typing as t
from types import ModuleType

import click

from piccolo.migrations.table import Migration
from piccolo.commands.migration.utils import (
    get_migration_modules,
    get_migration_ids,
)


class BackwardsMigrationManager:
    def __init__(self, migration_name: str):
        self.migrations_folder = os.path.join(os.getcwd(), "migrations")
        self.migration_modules: t.Dict[str, ModuleType] = {}
        self.migration_name = migration_name

    def run(self):
        self.migration_modules = get_migration_modules(self.migrations_folder)

        migration_ids = get_migration_ids(self.migration_modules)

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
            _sorted = _sorted[_sorted.index(self.migration_name) :]
            _sorted.reverse()

            already_ran = Migration.get_migrations_which_ran()

            for migration_name in _sorted:
                if migration_name not in already_ran:
                    print(
                        f"Migration {migration_name} hasn't run yet, can't "
                        "undo!"
                    )
                    sys.exit(1)

                print(f"Reversing {migration_name}")
                asyncio.run(
                    self.migration_modules[migration_name].backwards()
                )  # type: ignore

                Migration.delete().where(
                    Migration.name == migration_name
                ).run_sync()
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
