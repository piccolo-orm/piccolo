from piccolo.apps.migrations.auto.migration_manager import MigrationManager

ID = "2024-06-19T18:11:05:793132"
VERSION = "1.11.0"
DESCRIPTION = "An example fake migration"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="", description=DESCRIPTION, fake=True
    )

    def run():
        # This should never run, as this migrations is `fake=True`. It's here
        # for testing purposes (to make sure it never gets triggered).
        print("Running fake migration")

    manager.add_raw(run)

    return manager
