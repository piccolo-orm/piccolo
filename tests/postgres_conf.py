import os

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(
    config={
        "host": os.environ.get("PG_HOST", "localhost"),
        "port": os.environ.get("PG_PORT", "5432"),
        "user": os.environ.get("PG_USER", "postgres"),
        "password": os.environ.get("PG_PASSWORD", ""),
        "database": os.environ.get("PG_DATABASE", "piccolo"),
    }
)


APP_REGISTRY = AppRegistry(
    apps=[
        "tests.example_apps.music.piccolo_app",
        "tests.example_apps.mega.piccolo_app",
    ]
)
