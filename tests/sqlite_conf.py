from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine

DB = SQLiteEngine(path="test.sqlite")


APP_REGISTRY = AppRegistry(
    apps=[
        "tests.example_apps.music.piccolo_app",
        "tests.example_apps.mega.piccolo_app",
    ]
)
