from __future__ import annotations

import typing as t

from piccolo.apps.fixtures.commands.shared import (
    FixtureConfig,
    create_pydantic_fixture_model,
)
from piccolo.conf.apps import Finder
from piccolo.table import sort_table_classes


async def get_dump(
    fixture_configs: t.List[FixtureConfig],
) -> t.Dict[str, t.Any]:
    """
    Gets the data for each table specified and returns a data structure like:

    .. code-block:: python

        {
            'my_app_name': {
                'MyTableName': [
                    {
                        'id': 1,
                        'my_column_name': 'foo'
                    }
                ]
            }
        }

    """
    finder = Finder()

    output: t.Dict[str, t.Any] = {}

    for fixture_config in fixture_configs:
        app_config = finder.get_app_config(app_name=fixture_config.app_name)
        table_classes = [
            i
            for i in app_config.table_classes
            if i.__name__ in fixture_config.table_class_names
        ]
        sorted_table_classes = sort_table_classes(table_classes)

        output[fixture_config.app_name] = {}

        for table_class in sorted_table_classes:
            data = await table_class.select().run()
            output[fixture_config.app_name][table_class.__name__] = data

    return output


async def dump_to_json_string(
    fixture_configs: t.List[FixtureConfig],
) -> str:
    """
    Dumps all of the data for the given tables into a JSON string.
    """
    dump = await get_dump(fixture_configs=fixture_configs)
    pydantic_model = create_pydantic_fixture_model(
        fixture_configs=fixture_configs
    )
    return pydantic_model(**dump).json()


def parse_args(apps: str, tables: str) -> t.List[FixtureConfig]:
    """
    Works out which apps and tables the user is referring to.
    """
    finder = Finder()
    app_names = []

    if apps == "all":
        app_names = finder.get_sorted_app_names()
    elif "," in apps:
        app_names = apps.split(",")
    else:
        # Must be a single app name
        app_names.append(apps)

    table_class_names: t.Optional[t.List[str]] = None

    if tables != "all":
        table_class_names = tables.split(",") if "," in tables else [tables]
    output: t.List[FixtureConfig] = []

    for app_name in app_names:
        app_config = finder.get_app_config(app_name=app_name)
        table_classes = app_config.table_classes

        if table_class_names is None:
            fixture_configs = [i.__name__ for i in table_classes]
        else:
            fixture_configs = [
                i.__name__
                for i in table_classes
                if i.__name__ in table_class_names
            ]
        output.append(
            FixtureConfig(
                app_name=app_name,
                table_class_names=fixture_configs,
            )
        )

    return output


async def dump(apps: str = "all", tables: str = "all"):
    """
    Serialises the data from the given Piccolo apps / tables, and prints it
    out.

    :param apps:
        For all apps, specify `all`. For specific apps, pass in a comma
        separated list e.g. `blog,profiles,billing`. For a single app, just
        pass in the name of that app, e.g. `blog`.
    :param tables:
        For all tables, specify `all`. For specific tables, pass in a comma
        separated list e.g. `Post,Tag`. For a single app, just
        pass in the name of that app, e.g. `Post`.

    """
    fixture_configs = parse_args(apps=apps, tables=tables)
    json_string = await dump_to_json_string(fixture_configs=fixture_configs)
    print(json_string)
