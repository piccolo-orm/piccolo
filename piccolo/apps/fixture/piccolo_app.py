from piccolo.conf.apps import AppConfig

from .commands.dump import dump

APP_CONFIG = AppConfig(
    app_name="fixtures",
    migrations_folder_path="",
    table_classes=[],
    migration_dependencies=[],
    commands=[dump],
)
