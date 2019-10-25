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


MIGRATIONS_FOLDER = os.path.join(os.getcwd(), "migrations")
MIGRATION_MODULES: t.Dict[str, ModuleType] = {}


def _create_migrations_folder() -> bool:
    """
    Creates the folder that migrations live in. Returns True/False depending
    on whether it was created or not.
    """
    if os.path.exists(MIGRATIONS_FOLDER):
        return False
    else:
        os.mkdir(MIGRATIONS_FOLDER)
        for filename in ("__init__.py", "config.py"):
            with open(os.path.join(MIGRATIONS_FOLDER, filename), "w"):
                pass
        return True


def _create_new_migration() -> None:
    """
    Creates a new migration file on disk.
    """
    _id = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    path = os.path.join(MIGRATIONS_FOLDER, f"{_id}.py")
    with open(path, "w") as f:
        f.write(TEMPLATE.format(migration_id=_id))


###############################################################################


@click.option(
    "-c",
    "--create",
    multiple=True,
    help="Path to a table class which you want to create, e.g. tables.Band",
)
@click.command()
def new(create: t.Tuple[str]):
    """
    Creates a new file like migrations/2018-09-04T19:44:09.py
    """
    print("Creating new migration ...")

    for path in create:
        module_path, table_name = path.rsplit(".", maxsplit=1)
        module = importlib.import_module(module_path)
        try:
            table_class: Table = getattr(module, table_name)
        except AttributeError:
            print(f"Unable to find {path} - aborting")
            sys.exit(1)

        print(table_class._table_str())

    _create_migrations_folder()
    _create_new_migration()
