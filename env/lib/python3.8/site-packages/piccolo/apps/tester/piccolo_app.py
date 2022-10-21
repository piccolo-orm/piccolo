from piccolo.conf.apps import AppConfig

from .commands.run import run

APP_CONFIG = AppConfig(
    app_name="tester",
    migrations_folder_path="",
    table_classes=[],
    migration_dependencies=[],
    commands=[run],
)
