from piccolo.conf.apps import Finder
from piccolo.engine import engine_finder
from piccolo.utils.encoding import load_json


async def load_json_string(json_string: str):
    deserialised_contents = load_json(json_string)

    finder = Finder()
    engine = engine_finder()

    if not engine:
        raise Exception("Unable to find the engine.")

    async with engine.transaction():
        for app_name, table_dict in deserialised_contents.items():
            for table_class_name, data in table_dict.items():
                table_class = finder.get_table_with_name(
                    app_name, table_class_name
                )
                await table_class.insert(*[table_class(**row) for row in data])


async def load(path: str = "fixture.json"):
    """
    Reads the fixture file, and loads the contents into the database.
    """
    with open(path, "r") as f:
        contents = f.read()

    await load_json_string(contents)
