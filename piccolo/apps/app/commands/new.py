from __future__ import annotations

import importlib
import os
import pathlib
import string
import sys
import typing as t

import black
import jinja2

from piccolo.conf.apps import PiccoloConfUpdater

TEMPLATE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIRECTORY),
)


def module_exists(module_name: str) -> bool:
    """
    Check whether a Python module already exists with this name - for
    example, a builtin module.
    """
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError:
        return False
    else:
        return True


APP_NAME_ALLOWED_CHARACTERS = [*string.ascii_lowercase, *string.digits, "_"]


def validate_app_name(app_name: str):
    """
    Make sure the app name is something which is a valid Python package name.

    :raises ValueError:
        If ``app_name`` isn't valid.

    """
    for char in app_name:
        if not char.lower() in APP_NAME_ALLOWED_CHARACTERS:
            raise ValueError(
                f"The app name contains a disallowed character: `{char}`. "
                "It must only include a-z, 0-9, and _ characters."
            )


def get_app_module(app_name: str, root: str) -> str:
    return ".".join([*pathlib.Path(root).parts, app_name, "piccolo_app"])


def new_app(app_name: str, root: str = ".", register: bool = False):
    print(f"Creating {app_name} app ...")

    try:
        validate_app_name(app_name=app_name)
    except ValueError as exception:
        sys.exit(str(exception))

    if module_exists(app_name):
        sys.exit(
            f"A module called {app_name} already exists - possibly a builtin "
            "Python module. Please choose a different name for your app."
        )

    app_root = os.path.join(root, app_name)

    if os.path.exists(app_root):
        sys.exit("Folder already exists - exiting.")

    os.makedirs(app_root)

    with open(os.path.join(app_root, "__init__.py"), "w"):
        pass

    templates: t.Dict[str, t.Any] = {
        "piccolo_app.py": {"app_name": app_name},
        "tables.py": {},
    }

    for filename, context in templates.items():
        with open(os.path.join(app_root, filename), "w") as f:
            template = JINJA_ENV.get_template(f"{filename}.jinja")
            file_contents = template.render(**context)
            file_contents = black.format_str(
                file_contents, mode=black.FileMode(line_length=80)
            )
            f.write(file_contents)

    migrations_folder_path = os.path.join(app_root, "piccolo_migrations")
    os.mkdir(migrations_folder_path)

    with open(os.path.join(migrations_folder_path, "__init__.py"), "w"):
        pass

    if register:
        app_module = get_app_module(app_name=app_name, root=root)
        PiccoloConfUpdater().register_app(app_module=app_module)


def new(app_name: str, root: str = ".", register: bool = False):
    """
    Creates a new Piccolo app.

    :param app_name:
        The name of the new app.
    :param root:
        Where to create the app e.g. ./my/folder. By default it creates the
        app in the current directory.
    :param register:
        If True, the app is registered automatically in piccolo_conf.py.

    """
    new_app(app_name=app_name, root=root, register=register)
