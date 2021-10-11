from piccolo.apps.migrations.auto import MigrationManager

ID = "2020-12-17T18:44:44"
VERSION = "0.14.7"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="music")

    manager.add_table("Poster", tablename="poster")

    manager.add_column(
        table_class_name="Poster",
        tablename="poster",
        column_name="content",
        column_class_name="Text",
        params={
            "default": "",
            "null": False,
            "primary": False,
            "key": False,
            "unique": False,
            "index": False,
        },
    )

    return manager
