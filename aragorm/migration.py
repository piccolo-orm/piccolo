#!/usr/bin/env python

# For now ... just get initial sync working ...
# Need to know which tables to observe ...
# In Django there's a convention for having tables in tables.py ...
# assume there's an asjacent tables.py file to the migrations folder
# when creating migrations ... just specify a folder
# What happens if a project has multiple migrations in it ...
# If one migration file imports tables from another ... it becomes tricky
# Just have on migration.py folder ... and import the classes you want to
# manage ...
# start by creating migrate command ...

import inspect
import os
import importlib.util

import click

from aragorm.table import Table


def create_migrations_folder(directory: str) -> bool:
    path = os.path.join(directory, 'migrations')
    if os.path.exists(path):
        return False
    else:
        os.mkdir(path)
        with open(os.path.join(path, '__init__.py'), 'w'):
            pass
        return True


@click.command()
@click.argument('directory')
def migration(directory):
    """Make and run migrations"""
    directory = '' if (directory == '.') else directory

    tables_dir = os.path.join(
        os.getcwd(),
        directory
    )

    tables_file = os.path.join(
        tables_dir,
        'tables.py'
    )

    if not os.path.exists(tables_file):
        raise ValueError("Can't find tables.py!")

    spec = importlib.util.spec_from_file_location("tables", tables_file)
    tables = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tables)

    table_classes = []

    for name, element in tables.__dict__.items():
        if inspect.isclass(element) and issubclass(element, Table) and (element != Table):
            table_classes.append(element)

    print(table_classes)

    create_migrations_folder(tables_dir)
    # next ... if empty ... create initial commit ...
    # Get the class ... and


if __name__ == '__main__':
    migration()
