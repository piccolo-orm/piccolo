from __future__ import annotations
import os
import sys

import black
import jinja2


TEMPLATE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIRECTORY),
    trim_blocks=True,
    lstrip_blocks=True,
)


def new_piccolo_conf(engine_name: str, force: bool = False):
    print(f"Creating new piccolo_conf file ...")

    if os.path.exists("piccolo_conf.py") and not force:
        print("The file already exists - exiting.")
        sys.exit(1)

    with open("piccolo_conf.py", "w") as f:
        template = JINJA_ENV.get_template("piccolo_conf.py.jinja")
        file_contents = template.render(engine_name=engine_name)
        file_contents = black.format_str(
            file_contents, mode=black.FileMode(line_length=82)
        )

        f.write(file_contents)


def new(engine: str = "postgres", force: bool = False):
    """
    Creates a new Piccolo project file (piccolo_conf.py).

    :param engine:
        Which database backend you plan on using - options are sqlite or
        postgres.
    :param force:
        If True, it will override the piccolo_conf.py file if it already
        exists.

    """
    new_piccolo_conf(engine_name=engine, force=force)
