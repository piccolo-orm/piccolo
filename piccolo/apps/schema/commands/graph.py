import dataclasses
import os
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


def graph():
    finder = Finder()
    app_names = finder.get_sorted_app_names()

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

    template = render_template(tables=tables, relations=relations)

    print(template)
