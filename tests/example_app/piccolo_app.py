from piccolo.conf.apps import AppConfig

from .tables import Manager, Band, Venue, Concert, Ticket, Poster


APP_CONFIG = AppConfig(
    app_name="example_app",
    table_classes=[Manager, Band, Venue, Concert, Ticket, Poster],
    migrations_folder_path="",
    commands=[],
)
