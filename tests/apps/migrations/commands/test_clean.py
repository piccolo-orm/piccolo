from unittest import TestCase

from piccolo.apps.migrations.commands.clean import clean
from piccolo.apps.migrations.tables import Migration
from piccolo.utils.sync import run_sync


class TestCleanMigrationCommand(TestCase):
    def test_clean(self):
        Migration.create_table(if_not_exists=True).run_sync()

        real_migration_ids = [
            "2020-12-17T18:44:30",
            "2020-12-17T18:44:39",
            "2020-12-17T18:44:44",
        ]

        orphaned_migration_id = "2010-01-101T00:00:00"

        migration_ids = real_migration_ids + [orphaned_migration_id]

        Migration.insert(
            *[Migration(name=i, app_name="music") for i in migration_ids]
        ).run_sync()

        run_sync(clean(app_name="music", auto_agree=True))

        remaining_rows = (
            Migration.select(Migration.name)
            .where(Migration.app_name == "music")
            .output(as_list=True)
            .order_by(Migration.name)
            .run_sync()
        )
        self.assertEqual(remaining_rows, real_migration_ids)

        Migration.alter().drop_table(if_exists=True).run_sync()
