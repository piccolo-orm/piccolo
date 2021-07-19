from piccolo.apps.migrations.auto import MigrationManager


ID = "2021-07-19T12:40:31:140762"
VERSION = "0.26.0"


async def forwards():
    manager = MigrationManager(migration_id=ID, app_name="example_app")

    manager.drop_column(
        table_class_name="Manager", tablename="manager", column_name="name"
    )

    manager.drop_column(
        table_class_name="Band", tablename="band", column_name="popularity"
    )

    manager.drop_column(
        table_class_name="Band", tablename="band", column_name="manager"
    )

    manager.drop_column(
        table_class_name="Band", tablename="band", column_name="name"
    )

    manager.drop_column(
        table_class_name="Venue", tablename="venue", column_name="capacity"
    )

    manager.drop_column(
        table_class_name="Venue", tablename="venue", column_name="name"
    )

    manager.drop_column(
        table_class_name="Concert", tablename="concert", column_name="band_2"
    )

    manager.drop_column(
        table_class_name="Concert", tablename="concert", column_name="band_1"
    )

    manager.drop_column(
        table_class_name="Concert", tablename="concert", column_name="venue"
    )

    manager.drop_column(
        table_class_name="Ticket", tablename="ticket", column_name="price"
    )

    manager.drop_column(
        table_class_name="Poster", tablename="poster", column_name="content"
    )

    return manager
