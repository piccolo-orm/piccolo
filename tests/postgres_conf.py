from piccolo.engine.postgres import PostgresEngine


DB = PostgresEngine(
    {
        "host": "localhost",
        "database": "piccolo",
        "user": "piccolo",
        "password": "piccolo",
    }
)
