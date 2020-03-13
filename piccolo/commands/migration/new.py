from __future__ import annotations
import asyncio
import datetime
import os
import typing as t
from types import ModuleType

import click

from piccolo.commands.migration.base import BaseMigrationManager
from piccolo.migrations.auto import (
    SchemaSnapshot,
    MigrationManager,
    DiffableTable,
    SchemaDiffer,
)
from piccolo.migrations.template import render_template


MIGRATION_MODULES: t.Dict[str, ModuleType] = {}


def _create_migrations_folder(migrations_path: str) -> bool:
    """
    Creates the folder that migrations live in. Returns True/False depending
    on whether it was created or not.
    """
    if os.path.exists(migrations_path):
        return False
    else:
        os.mkdir(migrations_path)
        for filename in ("__init__.py", "config.py"):
            with open(os.path.join(migrations_path, filename), "w"):
                pass
        return True


def _create_new_migration(migrations_path: str, auto=False) -> None:
    """
    Creates a new migration file on disk.
    """
    _id = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    path = os.path.join(migrations_path, f"{_id}.py")
    with open(path, "w") as f:
        if auto:
            alter_statements = AutoMigrationManager().get_alter_statements()
            f.write(
                render_template(
                    migration_id=_id,
                    auto=True,
                    alter_statements=alter_statements,
                )
            )
        else:
            f.write(render_template(migration_id=_id, auto=False))


###############################################################################


class AutoMigrationManager(BaseMigrationManager):
    def get_alter_statements(self):
        """
        Works out which alter statements are required.
        """
        alter_statements: t.List[str] = []

        for config_module in self.get_config_modules():
            migrations_folder = os.path.dirname(config_module.__file__)

            migration_modules: t.Dict[
                str, MigrationModule
            ] = self.get_migration_modules(migrations_folder)

            migration_managers: t.List[MigrationManager] = []

            for _, migration_module in migration_modules.items():
                response = asyncio.run(migration_module.forwards())
                if isinstance(response, MigrationManager):
                    migration_managers.append(response)

            schema_snapshot = SchemaSnapshot(migration_managers)
            snapshot = schema_snapshot.get_snapshot()

            # Now get the current schema:
            current_diffable_tables = [
                DiffableTable(
                    class_name=i.__name__,
                    tablename=i._meta.tablename,
                    columns=i._meta.columns,
                )
                for i in TABLE_REGISTRY
            ]

            # Compare the current schema with the snapshot
            differ = SchemaDiffer(
                schema=current_diffable_tables, schema_snapshot=snapshot
            )
            alter_statements = differ.get_alter_statements()

        return alter_statements


###############################################################################


@click.option(
    "-p",
    "--path",
    multiple=False,
    help="The parent of the migrations folder e.g. ./my_app",
)
@click.option(
    "--auto", is_flag=True, help="Auto create the migration contents."
)
@click.command()
def new(path: str, auto: bool):
    """
    Creates a new file like migrations/2018-09-04T19:44:09.py
    """
    print("Creating new migration ...")

    root_dir = path if path else os.getcwd()
    migrations_path = os.path.join(root_dir, "migrations")

    _create_migrations_folder(migrations_path)
    _create_new_migration(migrations_path, auto=auto)
