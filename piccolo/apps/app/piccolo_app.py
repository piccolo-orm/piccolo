from piccolo.conf.apps import AppConfig, Command

from .commands.new import new
from .commands.show_all import show_all

APP_CONFIG = AppConfig(
    app_name="app",
    migrations_folder_path="",
    commands=[
        Command(callable=new, aliases=["create"]),
        Command(callable=show_all, aliases=["show", "all", "list"]),
    ],
)
