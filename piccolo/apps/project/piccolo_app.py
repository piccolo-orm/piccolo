from piccolo.conf.apps import AppConfig, Command

from .commands.new import new

APP_CONFIG = AppConfig(
    app_name="project",
    migrations_folder_path="",
    commands=[Command(callable=new, aliases=["create"])],
)
