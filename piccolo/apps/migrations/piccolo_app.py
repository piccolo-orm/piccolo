from piccolo.conf.apps import AppConfig, Command

from .commands.backwards import backwards
from .commands.check import check
from .commands.clean import clean
from .commands.forwards import forwards
from .commands.new import new

APP_CONFIG = AppConfig(
    app_name="migrations",
    migrations_folder_path="",
    commands=[
        Command(callable=backwards, aliases=["b", "back", "backward"]),
        Command(callable=check),
        Command(callable=clean),
        Command(callable=forwards, aliases=["f", "forward"]),
        Command(callable=new, aliases=["n", "create"]),
    ],
)
