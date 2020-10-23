import sys
import typing as t

from piccolo.conf.apps import AppRegistry, AppConfig, Finder
from piccolo.table import Table


def start_ipython_shell(**tables: t.Dict[str, t.Type[Table]]):
    try:
        import IPython
    except ImportError:
        print(
            "Install iPython using `pip install ipython==7.6.1` to use this "
            "feature."
        )
        sys.exit(1)

    existing_global_names = globals().keys()
    for table_class_name, table_class in tables.items():
        if table_class_name not in existing_global_names:
            globals()[table_class_name] = table_class

    IPython.embed()


def run():
    """
    Runs an iPython shell, and automatically imports all of the Table classes
    from your project.
    """
    app_registry: AppRegistry = Finder().get_app_registry()

    tables = {}
    spacer = "-------"

    if app_registry.app_configs:
        print(spacer)

        for app_name, app_config in app_registry.app_configs.items():
            app_config: AppConfig = app_config
            print(f"Importing {app_name} tables:")
            if app_config.table_classes:
                for table_class in app_config.table_classes:
                    table_class_name = table_class.__name__
                    print(f"- {table_class_name}")
                    tables[table_class_name] = table_class
            else:
                print("- None")

        print(spacer)

    start_ipython_shell(**tables)
