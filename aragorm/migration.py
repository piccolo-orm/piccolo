#!/usr/bin/env python

import datetime
import os

import click

from aragorm.table import Table
from aragorm.migrations.template import TEMPLATE


MIGRATIONS_FOLDER = os.path.join(os.getcwd(), 'migrations')


def _create_migrations_folder() -> bool:
    if os.path.exists(MIGRATIONS_FOLDER):
        return False
    else:
        os.mkdir(path)
        with open(os.path.join(MIGRATIONS_FOLDER, '__init__.py'), 'w'):
            pass
        return True


def _create_new_migration():
    _id = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    path = os.path.join(MIGRATIONS_FOLDER, f'{_id}.py')
    with open(path, 'w') as f:
        f.write(TEMPLATE.format(migration_id=_id))


@click.group()
def cli():
    pass


@click.command()
def new():
    """
    Creates a new file like migrations/0001_add_user_table.py
    """
    print('Creating new migration ...')
    _create_migrations_folder()
    _create_new_migration()


@click.command()
def run():
    """
    Runs any migrations which haven't been run yet, or up to a specific
    migration.
    """
    print('Running migrations ...')


cli.add_command(new)
cli.add_command(run)


if __name__ == '__main__':
    cli()
