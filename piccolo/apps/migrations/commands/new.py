from __future__ import annotations
import datetime
import os
import sys
import typing as t
from types import ModuleType

import black
import jinja2

from .base import BaseMigrationManager
from piccolo.conf.apps import AppConfig, AppRegistry
from piccolo.apps.migrations.auto import (
    SchemaSnapshot,
    DiffableTable,
    SchemaDiffer,
)
from piccolo.engine import SQLiteEngine


TEMPLATE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIRECTORY),
)


MIGRATION_MODULES: t.Dict[str, ModuleType] = {}


def render_template(**kwargs):
    template = JINJA_ENV.get_template("migration.py.jinja")
    return template.render(**kwargs)


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


def _create_new_migration(app_config: AppConfig, auto=False) -> None:
    """
    Creates a new migration file on disk.
    """
    _id = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    path = os.path.join(app_config.migrations_folder_path, f"{_id}.py")

    if auto:
        alter_statements = AutoMigrationManager().get_alter_statements(
            app_config=app_config
        )

        if len(alter_statements) == 0:
            print("No changes detected - exiting.")
            sys.exit(1)

        file_contents = render_template(
            migration_id=_id,
            auto=True,
            alter_statements=alter_statements,
            app_name=app_config.app_name,
        )
    else:
        file_contents = render_template(migration_id=_id, auto=False)

    # Beautify the file contents a bit.
    file_contents = black.format_str(
        file_contents, mode=black.FileMode(line_length=82)
    )

    with open(path, "w") as f:
        f.write(file_contents)


###############################################################################


class AutoMigrationManager(BaseMigrationManager):
    def get_alter_statements(self, app_config: AppConfig) -> t.List[str]:
        """
        Works out which alter statements are required.
        """
        alter_statements: t.List[str] = []

        migration_managers = self.get_migration_managers(
            app_name=app_config.app_name
        )

        schema_snapshot = SchemaSnapshot(migration_managers)
        snapshot = schema_snapshot.get_snapshot()

        # Now get the current schema:
        current_diffable_tables = [
            DiffableTable(
                class_name=i.__name__,
                tablename=i._meta.tablename,
                columns=i._meta.non_default_columns,
            )
            for i in app_config.table_classes
        ]

        # Compare the current schema with the snapshot
        differ = SchemaDiffer(
            schema=current_diffable_tables, schema_snapshot=snapshot
        )
        alter_statements = differ.get_alter_statements()

        return alter_statements


###############################################################################


def new(app_name: str, auto: bool = False):
    """
    Creates a new migration file in the migrations folder.

    :param app_name:
        The app to create a migration for.
    :param auto:
        Auto create the migration contents.

    """
    print("Creating new migration ...")

    try:
        import piccolo_conf
    except ImportError:
        print("Can't find piccolo_conf")
        sys.exit(1)

    if auto and isinstance(getattr(piccolo_conf, "DB"), SQLiteEngine):
        print("Auto migrations aren't currently supported by SQLite.")
        sys.exit(1)

    try:
        app_registry: AppRegistry = piccolo_conf.APP_REGISTRY
    except AttributeError:
        print("APP_REGISTRY isn't defined in piccolo_conf")
        sys.exit(1)

    app_config = app_registry.get_app_config(app_name)

    if not app_config:
        raise ValueError(f"Unrecognised app_name: {app_name}")

    _create_migrations_folder(app_config.migrations_folder_path)
    _create_new_migration(app_config=app_config, auto=auto)
