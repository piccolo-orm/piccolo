import os
import sys
import pprint

import click

from piccolo.commands.migration.utils import get_migration_modules


MIGRATIONS_FOLDER = os.path.join(os.getcwd(), "migrations")


@click.command()
def check():
    """
    Lists all migrations which have and haven't ran.
    """
    print("Listing migrations ...")

    migration_modules = get_migration_modules(
        MIGRATIONS_FOLDER, recursive=True
    )

    pprint.pprint(list(migration_modules.keys()), indent=4)
