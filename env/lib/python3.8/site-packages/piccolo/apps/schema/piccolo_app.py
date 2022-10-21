from piccolo.conf.apps import AppConfig, Command

from .commands.generate import generate
from .commands.graph import graph

APP_CONFIG = AppConfig(
    app_name="schema",
    migrations_folder_path="",
    commands=[
        Command(callable=generate, aliases=["gen", "create", "new", "mirror"]),
        Command(
            callable=graph,
            aliases=["map", "visualise", "vizualise", "viz", "vis"],
        ),
    ],
)
