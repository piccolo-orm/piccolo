from piccolo.conf.apps import AppConfig, Command

from .commands.generate import generate

APP_CONFIG = AppConfig(
    app_name="schema",
    migrations_folder_path="",
    commands=[Command(callable=generate, aliases=["g", "create", "new"])],
)
