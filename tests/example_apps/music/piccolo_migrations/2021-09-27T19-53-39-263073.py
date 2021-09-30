from piccolo.apps.migrations.auto import MigrationManager


ID = "2021-09-27T19:53:39:263073"
VERSION = "0.51.1"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="example_app", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="Shirt", tablename="shirt", column_name="size2"
    )

    manager.drop_column(
        table_class_name="Shirt", tablename="shirt", column_name="size3"
    )

    return manager
