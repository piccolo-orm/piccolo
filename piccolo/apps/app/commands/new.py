from __future__ import annotations
import os
import sys
import typing as t

import black
import jinja2


TEMPLATE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIRECTORY),
)


def new_app(app_name: str):
    print(f"Creating {app_name} app ...")
    if os.path.exists(app_name):
        print("Folder already exists - exiting.")
        sys.exit(1)
    os.mkdir(app_name)

    with open(os.path.join(app_name, "__init__.py"), "w"):
        pass

    templates: t.Dict[str, t.Any] = {
        "piccolo_app.py": {"app_name": app_name},
        "tables.py": {},
    }

    for filename, context in templates.items():
        with open(os.path.join(app_name, filename), "w") as f:
            template = JINJA_ENV.get_template(filename + ".jinja")
            file_contents = template.render(**context)
            file_contents = black.format_str(
                file_contents, mode=black.FileMode(line_length=80)
            )
            f.write(file_contents)

    migrations_folder_path = os.path.join(app_name, "piccolo_migrations")
    os.mkdir(migrations_folder_path)

    with open(os.path.join(migrations_folder_path, "__init__.py"), "w"):
        pass


def new(app_name: str):
    """
    Creates a new Piccolo app.

    :param app_name:
        The name of the new app.
    """
    new_app(app_name)
