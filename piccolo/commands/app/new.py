from __future__ import annotations
import os
import sys

import click


@click.argument("app_name")
@click.command()
def new(app_name: str):
    """
    Creates a new Piccolo app.
    """
    print(f"Creating {app_name} app ...")
    if os.path.exists(app_name):
        print("Folder already exists - exiting.")
        sys.exit(1)
    os.mkdir(app_name)

    filenames = ("__init__.py", "piccolo_app.py", "tables.py")

    for filename in filenames:
        with open(os.path.join(app_name, filename), "w"):
            pass

    migrations_folder_path = os.path.join(app_name, "piccolo_migrations")
    os.mkdir(migrations_folder_path)

    with open(os.path.join(migrations_folder_path, "__init__.py"), "w"):
        pass
