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
    options={
        # By default the migration table is created in the public schema - you
        # can override this if you want the migration table to be created in
        # a different schema.
        "schema": None,
        # You can override the name of the migration table if it clashes
        # with an existing table in the database.
        "tablename": None,
    },
)
