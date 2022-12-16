from __future__ import annotations

import datetime
import os
import string
import sys
import typing as t
from dataclasses import dataclass
from itertools import chain
from types import ModuleType

import black
import jinja2

from piccolo import __VERSION__
from piccolo.apps.migrations.auto import (
    AlterStatements,
    DiffableTable,
    SchemaDiffer,
    SchemaSnapshot,
)
from piccolo.conf.apps import AppConfig, Finder
from piccolo.engine import SQLiteEngine

from .base import BaseMigrationManager

TEMPLATE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIRECTORY),
)

MIGRATION_MODULES: t.Dict[str, ModuleType] = {}

VALID_PYTHON_MODULE_CHARACTERS = string.ascii_lowercase + string.digits + "_"


def render_template(**kwargs):
    template = JINJA_ENV.get_template("migration.py.jinja")
    return template.render(version=__VERSION__, **kwargs)


def _create_migrations_folder(migrations_path: str) -> bool:
    """
    Creates the folder that migrations live in. Returns True/False depending
    on whether it was created or not.
    """
    if os.path.exists(migrations_path):
        return False
    os.mkdir(migrations_path)
    with open(os.path.join(migrations_path, "__init__.py"), "w"):
        pass
    return True


@dataclass
class NewMigrationMeta:
    migration_id: str
    migration_filename: str
    migration_path: str


def now():
    """
    In a separate function so it's easier to patch in tests.
    """
    return datetime.datetime.now()


def _generate_migration_meta(app_config: AppConfig) -> NewMigrationMeta:
    """
    Generates the migration ID and filename.
    """
    # The microseconds originally weren't part of the ID, but there was a
    # chance that the IDs would clash if the migrations are generated
    # programatically in quick succession (e.g. in a unit test), so they had
    # to be added. The trade off is a longer ID.
    _id = now().strftime("%Y-%m-%dT%H:%M:%S:%f")

    # Originally we just used the _id as the filename, but colons aren't
    # supported in Windows, so we need to sanitize it. We don't want to
    # change the _id format though, as it would break existing migrations.
    # The filename doesn't have any special significance - only the id matters.
    cleaned_id = _id.replace(":", "_").replace("-", "_").lower()

    # Just in case the app name contains characters which aren't valid for
    # a Python module.
    cleaned_app_name = "".join(
        [
            i
            for i in app_config.app_name.lower().replace("-", "_")
            if i in VALID_PYTHON_MODULE_CHARACTERS
        ]
    )

    filename = f"{cleaned_app_name}_{cleaned_id}"

    path = os.path.join(app_config.migrations_folder_path, f"{filename}.py")

    return NewMigrationMeta(
        migration_id=_id, migration_filename=filename, migration_path=path
    )


class NoChanges(Exception):
    pass


async def _create_new_migration(
    app_config: AppConfig,
    auto: bool = False,
    description: str = "",
    auto_input: t.Optional[str] = None,
) -> NewMigrationMeta:
    """
    Creates a new migration file on disk.
    """
    meta = _generate_migration_meta(app_config=app_config)

    if auto:
        alter_statements = await AutoMigrationManager(
            auto_input=auto_input
        ).get_alter_statements(app_config=app_config)

        _alter_statements = list(
            chain(*[i.statements for i in alter_statements])
        )
        extra_imports = sorted(
            set(chain(*[i.extra_imports for i in alter_statements])),
            key=lambda x: x.__repr__(),
        )
        extra_definitions = sorted(
            set(chain(*[i.extra_definitions for i in alter_statements])),
        )

        if sum(len(i.statements) for i in alter_statements) == 0:
            raise NoChanges()

        file_contents = render_template(
            migration_id=meta.migration_id,
            auto=True,
            alter_statements=_alter_statements,
            extra_imports=extra_imports,
            extra_definitions=extra_definitions,
            app_name=app_config.app_name,
            description=description,
        )
    else:
        file_contents = render_template(
            migration_id=meta.migration_id, auto=False, description=description
        )

    # Beautify the file contents a bit.
    file_contents = black.format_str(
        file_contents, mode=black.FileMode(line_length=82)
    )

    with open(meta.migration_path, "w") as f:
        f.write(file_contents)

    return meta


###############################################################################


class AutoMigrationManager(BaseMigrationManager):
    def __init__(self, auto_input: t.Optional[str] = None, *args, **kwargs):
        self.auto_input = auto_input
        super().__init__(*args, **kwargs)

    async def get_alter_statements(
        self, app_config: AppConfig
    ) -> t.List[AlterStatements]:
        """
        Works out which alter statements are required.
        """
        migration_managers = await self.get_migration_managers(
            app_config=app_config
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
            schema=current_diffable_tables,
            schema_snapshot=snapshot,
            auto_input=self.auto_input,
        )
        return differ.get_alter_statements()


###############################################################################


async def new(
    app_name: str,
    auto: bool = False,
    desc: str = "",
    auto_input: t.Optional[str] = None,
):
    """
    Creates a new migration file in the migrations folder.

    :param app_name:
        The app to create a migration for.
    :param auto:
        Auto create the migration contents.
    :param desc:
        A description of what the migration does, for example --desc='adding
        name column'.
    :param auto_input:
        If provided, all prompts for user input will automatically have this
        entered. For example, --auto_input='y'.

    """
    print("Creating new migration ...")

    engine = Finder().get_engine()
    if auto and isinstance(engine, SQLiteEngine):
        sys.exit("Auto migrations aren't currently supported by SQLite.")

    app_config = Finder().get_app_config(app_name=app_name)

    _create_migrations_folder(app_config.migrations_folder_path)
    try:
        await _create_new_migration(
            app_config=app_config,
            auto=auto,
            description=desc,
            auto_input=auto_input,
        )
    except NoChanges:
        print("No changes detected - exiting.")
        sys.exit(0)
