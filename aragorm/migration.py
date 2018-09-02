#!/usr/bin/env python

# For now ... just get initial sync working ...
# Need to know which models to observe ...
# In Django there's a convention for having models in models.py ...
# assume there's an asjacent models.py file to the migrations folder
# when creating migrations ... just specify a folder
# What happens if a project has multiple migrations in it ...
# If one migration file imports models from another ... it becomes tricky
# Just have on migration.py folder ... and import the classes you want to
# manage ...
# start by creating migrate command ...

import inspect
import os
import importlib.util

import click

from aragorm.model import Model


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

    models_dir = os.path.join(
        os.getcwd(),
        directory
    )

    models_file = os.path.join(
        models_dir,
        'models.py'
    )

    if not os.path.exists(models_file):
        raise ValueError("Can't find models.py!")

    spec = importlib.util.spec_from_file_location("models", models_file)
    models = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(models)

    model_classes = []

    for name, element in models.__dict__.items():
        if inspect.isclass(element) and issubclass(element, Model) and (element != Model):
            model_classes.append(element)

    print(model_classes)

    create_migrations_folder(models_dir)
    # next ... if empty ... create initial commit ...
    # Get the class ... and


if __name__ == '__main__':
    migration()
