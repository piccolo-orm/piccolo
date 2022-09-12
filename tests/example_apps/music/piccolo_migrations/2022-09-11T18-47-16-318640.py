from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.column_types import BigInt
from piccolo.columns.column_types import Integer


ID = "2022-09-11T18:47:16:318640"
VERSION = "0.88.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="music", description=DESCRIPTION
    )

    manager.alter_column(
        table_class_name="Band",
        tablename="band",
        column_name="popularity",
        db_column_name="popularity",
        params={},
        old_params={},
        column_class=BigInt,
        old_column_class=Integer,
    )

    return manager
