from __future__ import annotations

import typing as t

from piccolo.apps.fixtures.commands.shared import (
    FixtureConfig,
    create_pydantic_fixture_model,
)
from piccolo.conf.apps import Finder
from piccolo.engine import engine_finder
from piccolo.table import Table, sort_table_classes
from piccolo.utils.encoding import load_json
from piccolo.utils.list import batch


async def load_json_string(json_string: str, chunk_size: int = 1000):
    """
    Parses the JSON string, and inserts the parsed data into the database.
    """
    # We have to deserialise the JSON to find out which apps and tables it
    # contains, so we can create a Pydantic model.
    # Then we let Pydantic do the proper deserialisation, as it does a much
    # better job of deserialising dates, datetimes, bytes etc.
    deserialised_contents = load_json(json_string)

    app_names = deserialised_contents.keys()

    fixture_configs = [
        FixtureConfig(
            app_name=app_name,
            table_class_names=list(deserialised_contents[app_name].keys()),
        )
        for app_name in app_names
    ]
    pydantic_model_class = create_pydantic_fixture_model(
        fixture_configs=fixture_configs
    )

    fixture_pydantic_model = pydantic_model_class.parse_raw(json_string)

    finder = Finder()
    engine = engine_finder()

    if not engine:
        raise Exception("Unable to find the engine.")

    # This is what we want to the insert into the database:
    data: t.Dict[t.Type[Table], t.List[Table]] = {}

    for app_name in app_names:
        app_model = getattr(fixture_pydantic_model, app_name)

        for (
            table_class_name,
            model_instance_list,
        ) in app_model.__dict__.items():
            table_class = finder.get_table_with_name(
                app_name, table_class_name
            )
            data[table_class] = [
                table_class.from_dict(row.__dict__)
                for row in model_instance_list
            ]

    # We have to sort the table classes based on foreign key, so we insert
    # the data in the right order.
    sorted_table_classes = sort_table_classes(list(data.keys()))

    async with engine.transaction():
        for table_class in sorted_table_classes:
            rows = data[table_class]

            for chunk in batch(data=rows, chunk_size=chunk_size):
                await table_class.insert(*chunk).run()


async def load(path: str = "fixture.json", chunk_size: int = 1000):
    """
    Reads the fixture file, and loads the contents into the database.

    :param path:
        The path of the fixture file.

    :param chunk_size:
        The maximum number of rows to insert at a time. This is usually
        determined by the database adapter, which has a max number of
        parameters per query.

    """
    with open(path, "r") as f:
        contents = f.read()

    await load_json_string(contents, chunk_size=chunk_size)
