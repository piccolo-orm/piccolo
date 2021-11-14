from piccolo.apps.migrations.auto import MigrationManager
from piccolo.columns.column_types import Integer

ID = "2021-11-13T14:01:46:114725"
VERSION = "0.59.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="music", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="Venue",
        tablename="venue",
        column_name="capacity",
        params={"secret": True},
        old_params={"secret": False},
        column_class=Integer,
        old_column_class=Integer,
    )

    return manager
