import os

from piccolo.conf.apps import AppConfig

from .tables import (
    Band,
    Concert,
    Manager,
    Poster,
    RecordingStudio,
    Shirt,
    Ticket,
    Venue,
)

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


APP_CONFIG = AppConfig(
    app_name="example_app",
    table_classes=[
        Manager,
        Band,
        Venue,
        Concert,
        Ticket,
        Poster,
        Shirt,
        RecordingStudio,
    ],
    migrations_folder_path=os.path.join(
        CURRENT_DIRECTORY, "piccolo_migrations"
    ),
    commands=[],
)
