"""
Credit to the Django Extensions team for inspiring this tool.
"""

import dataclasses
import os
import sys
import typing as t

import jinja2

from piccolo.conf.apps import Finder

TEMPLATE_DIRECTORY = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath=TEMPLATE_DIRECTORY),
)


@dataclasses.dataclass
class GraphColumn:
    name: str
    type: str


@dataclasses.dataclass
class GraphTable:
    name: str
    columns: t.List[GraphColumn]


@dataclasses.dataclass
class GraphRelation:
    table_a: str
    table_b: str
    label: str


def render_template(**kwargs):
    template = JINJA_ENV.get_template("graphviz.dot.jinja")
    return template.render(**kwargs)


def graph(
    apps: str = "all", direction: str = "LR", output: t.Optional[str] = None
):
    """
    Prints out a graphviz .dot file for your schema.

    :param apps:
        The name of the apps to include. If 'all' is given then every app is
        included. To specify multiple app names, separate them with commas.
        For example --apps="app1,app2".
    :param direction:
        How the tables should be orientated - by default it's "LR" which is
        left to right, so the graph will be landscape. The alternative is
        "TB", which is top to bottom, so the graph will be portrait.
    :param output:
        If specified, rather than printing out the file contents, they'll be
        written to this file. For example --output=graph.dot

    """
    finder = Finder()
    app_names = finder.get_sorted_app_names()

    if apps != "all":
        given_app_names = [i.strip() for i in apps.split(",")]
        delta = set(given_app_names) - set(app_names)
        if delta:
            sys.exit(f"These apps aren't recognised: {', '.join(delta)}.")
        app_names = given_app_names

    tables: t.List[GraphTable] = []
    relations: t.List[GraphRelation] = []

    for app_name in app_names:
        app_config = finder.get_app_config(app_name=app_name)
        for table_class in app_config.table_classes:
            tables.append(
                GraphTable(
                    name=table_class.__name__,
                    columns=[
                        GraphColumn(
                            name=i._meta.name, type=i.__class__.__name__
                        )
                        for i in table_class._meta.columns
                    ],
                )
            )
            for fk_column in table_class._meta.foreign_key_columns:
                reference_table_class = (
                    fk_column._foreign_key_meta.resolved_references
                )
                relations.append(
                    GraphRelation(
                        table_a=table_class.__name__,
                        table_b=reference_table_class.__name__,
                        label=fk_column._meta.name,
                    )
                )

    contents = render_template(
        tables=tables, relations=relations, direction=direction
    )

    if output is None:
        print(contents)
    else:
        with open(output, "w") as f:
            f.write(contents)
