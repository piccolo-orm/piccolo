#!/usr/bin/env python

import datetime
import importlib.util
import os
import sys
from typing import List, Dict
from types import ModuleType

import click

from aragorm.migrations.template import TEMPLATE
from aragorm.migrations.table import Migration


MIGRATIONS_FOLDER = os.path.join(os.getcwd(), 'migrations')
MIGRATION_MODULES: Dict[str, ModuleType] = {}


def _create_migrations_folder() -> bool:
    if os.path.exists(MIGRATIONS_FOLDER):
        return False
    else:
        os.mkdir(MIGRATIONS_FOLDER)
        for filename in ('__init__.py', 'config.py'):
            with open(os.path.join(MIGRATIONS_FOLDER, filename), 'w'):
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


###############################################################################

def _create_migration_table() -> bool:
    if not Migration.table_exists().run_sync():
        Migration.create().run_sync()
        return True
    return False


def _get_migrations_which_ran() -> List[str]:
    """
    Returns the names of migrations which have already run.
    """
    return Migration.select('name').run_sync()


def _get_migration_modules() -> None:
    folder_contents = os.listdir(MIGRATIONS_FOLDER)
    excluded = ('__init__.py', 'config.py', '__pycache__')
    migration_names = [
        i.split('.py')[0] for i in folder_contents if i not in excluded
    ]
    modules = [importlib.import_module(name) for name in migration_names]
    global MIGRATION_MODULES
    for m in modules:
        _id = getattr(m, 'ID', None)
        if _id:
            MIGRATION_MODULES[_id] = m


def _get_migration_ids() -> List[str]:
    return list(MIGRATION_MODULES.keys())


def _get_config() -> dict:
    """
    A config file is required for the database credentials.
    """
    sys.path.insert(0, MIGRATIONS_FOLDER)

    config_file = os.path.join(MIGRATIONS_FOLDER, 'config.py')
    if not os.path.exists(config_file):
        raise Exception(f"Can't find config.py in {MIGRATIONS_FOLDER}")

    config = importlib.import_module('config')

    db = getattr(config, 'DB', None)
    if not db:
        raise Exception('config.py is missing a DB dictionary.')
    return db


@click.command()
def run():
    """
    Runs any migrations which haven't been run yet, or up to a specific
    migration.
    """
    print('Running migrations ...')
    sys.path.insert(0, os.getcwd())

    Migration.Meta.db = _get_config()

    _create_migration_table()

    already_ran = _get_migrations_which_ran()
    print(f'Already ran = {already_ran}')

    _get_migration_modules()
    ids = _get_migration_ids()
    print(f'Migration ids = {ids}')

    for _id in (set(ids) - set(already_ran)):
        MIGRATION_MODULES[_id].forwards()
        print(f'Ran {_id}')
        # When it has run, update migration DB ...


###############################################################################

cli.add_command(new)
cli.add_command(run)


if __name__ == '__main__':
    cli()
