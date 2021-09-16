from __future__ import annotations

from piccolo.apps.fixtures.commands.shared import (
    FixtureConfig,
    create_pydantic_fixture_model,
)
from piccolo.conf.apps import Finder
from piccolo.engine import engine_finder
from piccolo.utils.encoding import load_json


async def load_json_string(json_string: str):
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
            table_class_names=[
                i for i in deserialised_contents[app_name].keys()
            ],
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

    async with engine.transaction():
        for app_name in app_names:
            app_model = getattr(fixture_pydantic_model, app_name)

            for (
                table_class_name,
                model_instance_list,
            ) in app_model.__dict__.items():
                table_class = finder.get_table_with_name(
                    app_name, table_class_name
                )

                await table_class.insert(
                    *[
                        table_class(**row.__dict__)
                        for row in model_instance_list
                    ]
                ).run()


async def load(path: str = "fixture.json"):
    """
    Reads the fixture file, and loads the contents into the database.
    """
    with open(path, "r") as f:
        contents = f.read()

    await load_json_string(contents)
