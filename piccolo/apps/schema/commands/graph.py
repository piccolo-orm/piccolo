import dataclasses
import os
import typing as t

import jinja2

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
    table_a: GraphTable
    table_b: GraphTable
    label: str


def render_template(**kwargs):
    template = JINJA_ENV.get_template("graphviz.dot.jinja")
    return template.render(**kwargs)


def graph():
    table_a = GraphTable(
        name="TableA", columns=[GraphColumn(name="id", type="Serial")]
    )
    table_b = GraphTable(
        name="TableB", columns=[GraphColumn(name="id", type="Serial")]
    )

    relation = GraphRelation(table_a=table_a, table_b=table_b, label="foo")

    template = render_template(tables=[table_a, table_b], relations=[relation])

    print(template)
