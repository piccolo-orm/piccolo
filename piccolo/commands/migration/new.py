import datetime
import importlib
import importlib.util
import os
import sys
import typing as t
from types import ModuleType

import click

from piccolo.migrations.template import TEMPLATE
from piccolo.table import Table


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


def _create_new_migration(migrations_path) -> None:
    """
    Creates a new migration file on disk.
    """
    _id = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    path = os.path.join(migrations_path, f"{_id}.py")
    with open(path, "w") as f:
        f.write(TEMPLATE.format(migration_id=_id))


###############################################################################


@click.option(
    "-c",
    "--create",
    multiple=True,
    help="Path to a table class which you want to create, e.g. tables.Band",
)
@click.option(
    "-p",
    "--path",
    multiple=False,
    help="The parent of the migrations folder e.g. ./my_app",
)
@click.command()
def new(create: t.Tuple[str], path: str):
    """
    Creates a new file like migrations/2018-09-04T19:44:09.py
    """
    print("Creating new migration ...")

    root_dir = path if path else os.getcwd()
    migrations_path = os.path.join(root_dir, "migrations")

    # TODO - might remove this. Does nothing currently.
    for path in create:
        module_path, table_name = path.rsplit(".", maxsplit=1)
        module = importlib.import_module(module_path)
        try:
            table_class: Table = getattr(module, table_name)
        except AttributeError:
            print(f"Unable to find {path} - aborting")
            sys.exit(1)

        print(table_class._table_str())

    _create_migrations_folder(migrations_path)
    _create_new_migration(migrations_path)
