import typing as t

from piccolo.apps.migrations.auto.migration_manager import sort_table_classes
from piccolo.conf.apps import Finder
from piccolo.utils.encoding import dump_json


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
    finder = Finder()
    app_names = []

    ###########################################################################

    if apps == "all":
        app_names = finder.get_sorted_app_names()
    elif "," in apps:
        app_names = apps.split(",")
    else:
        # Must be a single app name
        app_names.append(apps)

    ###########################################################################

    output: t.Dict[str, t.Any] = {}

    for app_name in app_names:
        app_config = finder.get_app_config(app_name=app_name)
        table_classes = app_config.table_classes

        if tables != "all":
            if "," in tables:
                table_class_names = apps.split(",")
            else:
                # Must be a single table class name
                table_class_names = [tables]

            table_classes = [
                i for i in table_classes if i.__name__ in table_class_names
            ]

        # Sort the table classes based on their ForeignKey columns
        sorted_table_classes = sort_table_classes(table_classes)

        output[app_name] = {}

        for table_class in sorted_table_classes:
            data = await table_class.select().run()
            output[app_name][table_class.__name__] = data

    json_output = dump_json(output, pretty=True)
    print(json_output)
