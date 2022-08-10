from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns.constraints import UniqueConstraint


ID = "2022-08-10T16:19:25:729836"
VERSION = "0.82.0"
DESCRIPTION = ""


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="test_app", description=DESCRIPTION
    )

    manager.drop_column(
        table_class_name="FooTable",
        tablename="foo_table",
        column_name="my_test_constraint_1",
        db_column_name="my_test_constraint_1",
        column_class=UniqueConstraint,
    )

    return manager
