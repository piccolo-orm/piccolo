import os

from piccolo.conf.apps import AppConfig

from .tables import MegaTable, SmallTable

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="mega",
    table_classes=[MegaTable, SmallTable],
    migrations_folder_path=os.path.join(
        CURRENT_DIRECTORY, "piccolo_migrations"
    ),
    commands=[],
)
