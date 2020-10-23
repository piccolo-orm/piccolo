from piccolo.engine.sqlite import SQLiteEngine
from piccolo.conf.apps import AppRegistry


DB = SQLiteEngine(path="test.sqlite")


APP_REGISTRY = AppRegistry()
