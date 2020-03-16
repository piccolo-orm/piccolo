from __future__ import annotations
import os
import sys

import click
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
        rendered = template.render(engine_name=engine_name)
        f.write(rendered)


@click.option(
    "--engine",
    default="postgres",
    multiple=False,
    type=click.Choice(["sqlite", "postgres"], case_sensitive=False),
    help="Which database backend you plan on using.",
)
@click.option(
    "--force",
    is_flag=True,
    help=(
        "If True, it will override the piccolo_conf.py file if it already "
        "exists."
    ),
)
@click.command()
def new(engine, force):
    """
    Creates a new Piccolo app.
    """
    new_piccolo_conf(engine_name=engine, force=force)
