import os

from piccolo.conf.apps import AppRegistry
from piccolo.engine.mysql import MySQLEngine

DB = MySQLEngine(
    config={
        "host": os.environ.get("MY_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MY_PORT", 3306)),
        "user": os.environ.get("MY_USER", "root"),
        "password": os.environ.get("MY_PASSWORD", ""),
        "db": os.environ.get("MY_DATABASE", "piccolo"),
    }
)


APP_REGISTRY = AppRegistry(
    apps=[
        "tests.example_apps.music.piccolo_app",
        "tests.example_apps.mega.piccolo_app",
    ]
)
