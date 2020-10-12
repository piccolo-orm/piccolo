from piccolo.engine.postgres import PostgresEngine
from piccolo.conf.apps import AppRegistry


DB = PostgresEngine(
    {
        "host": "localhost",
        "database": "piccolo",
        "user": "piccolo",
        "password": "piccolo",
    }
)


APP_REGISTRY = AppRegistry()
