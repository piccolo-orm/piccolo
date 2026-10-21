from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.migrations.commands.backwards import backwards
from piccolo.apps.migrations.commands.base import BaseMigrationManager
from piccolo.apps.migrations.commands.forwards import forwards
from piccolo.apps.migrations.tables import Migration
from piccolo.conf.apps import Finder
from piccolo.utils.sync import run_sync
from tests.base import AsyncMock, engines_only
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Instrument,
    Manager,
    Poster,
    RecordingStudio,
    Shirt,
    Signing,
    Ticket,
    Venue,
)

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table

TABLE_CLASSES: list[type[Table]] = [
    Manager,
    Band,
    Venue,
    Concert,
    Ticket,
    Poster,
    Shirt,
    RecordingStudio,
    Instrument,
    Signing,
]


@engines_only("postgres", "cockroach")
class TestForwardsBackwards(TestCase):
    """
    Test the forwards and backwards migration commands.
    """

    def get_migration_names(self):
        app_config = Finder().get_app_config(app_name="music")
        finder = BaseMigrationManager()
        migration_modules_dict = finder.get_migration_modules(
            folder_path=app_config.migrations_folder_path.__str__()
        )
        return finder.get_migration_ids(
            migration_module_dict=migration_modules_dict
        )

    def test_forwards_backwards_all_migrations(self):
        """
        Test running all of the migrations forwards, then backwards.
        """
        for app_name in ("music", "all"):
            run_sync(forwards(app_name=app_name, migration_id="all"))

            # Check the tables exist
            for table_class in TABLE_CLASSES:
                self.assertTrue(table_class.table_exists().run_sync())
            self.assertNotEqual(Migration.count().run_sync(), 0)

            run_sync(
                backwards(
                    app_name=app_name, migration_id="all", auto_agree=True
                )
            )

            # Check the tables don't exist
            for table_class in TABLE_CLASSES:
                self.assertTrue(not table_class.table_exists().run_sync())
            self.assertEqual(Migration.count().run_sync(), 0)
            # Preview
            run_sync(
                forwards(app_name=app_name, migration_id="all", preview=True)
            )
            for table_class in TABLE_CLASSES:
                self.assertTrue(not table_class.table_exists().run_sync())
            self.assertEqual(Migration.count().run_sync(), 0)

    def test_forwards_backwards_single_migration(self):
        """
        Test running a single migrations forwards, then backwards.
        """
        table_classes = [Band, Manager]

        for migration_id in ["1", "2020-12-17T18:44:30"]:
            run_sync(forwards(app_name="music", migration_id=migration_id))

            # Check the tables exist
            for table_class in table_classes:
                self.assertTrue(table_class.table_exists().run_sync())

            self.assertTrue(
                Migration.exists()
                .where(Migration.name == "2020-12-17T18:44:30")
                .run_sync()
            )

            run_sync(
                backwards(
                    app_name="music",
                    migration_id=migration_id,
                    auto_agree=True,
                )
            )

            # Check the tables don't exist
            for table_class in table_classes:
                self.assertTrue(not table_class.table_exists().run_sync())
            self.assertFalse(
                Migration.exists()
                .where(Migration.name == "2020-12-17T18:44:30")
                .run_sync()
            )

            # Preview
            run_sync(
                forwards(
                    app_name="music", migration_id=migration_id, preview=True
                )
            )
            for table_class in table_classes:
                self.assertTrue(not table_class.table_exists().run_sync())
            self.assertFalse(
                Migration.exists()
                .where(Migration.name == "2020-12-17T18:44:30")
                .run_sync()
            )

    @patch("piccolo.apps.migrations.commands.forwards.print")
    def test_forwards_unknown_migration(self, print_: MagicMock):
        """
        Test running an unknown migrations forwards.
        """
        with self.assertRaises(SystemExit):
            run_sync(
                forwards(app_name="music", migration_id="migration-12345")
            )

        self.assertTrue(
            call("migration-12345 is unrecognised", file=sys.stderr)
            in print_.mock_calls
        )

    @patch("piccolo.apps.migrations.commands.forwards.print")
    @patch(
        "piccolo.apps.migrations.commands.forwards.Migration.get_migrations_which_ran",  # noqa: E501
        new_callable=AsyncMock,
    )
    def test_already_ran(
        self,
        get_migrations_which_ran: MagicMock,
        print_: MagicMock,
    ):
        """
        When a specific migration ID has already run, but there are later
        migrations which haven't, then the command should succeed rather than
        reporting the migration as unrecognised.

        https://github.com/piccolo-orm/piccolo/issues/1359

        """
        migration_id = "2020-12-17T18:44:30"

        get_migrations_which_ran.return_value = [migration_id]

        run_sync(forwards(app_name="music", migration_id=migration_id))

        self.assertIn(
            call(f"🏁 Migration {migration_id} has already been run"),
            print_.mock_calls,
        )

    @patch("piccolo.apps.migrations.commands.backwards.print")
    def test_backwards_unknown_migration(self, print_: MagicMock):
        """
        Test running an unknown migrations backwards.
        """
        run_sync(forwards(app_name="music", migration_id="all"))

        with self.assertRaises(SystemExit):
            run_sync(
                backwards(
                    app_name="music",
                    migration_id="migration-12345",
                    auto_agree=True,
                )
            )

        self.assertTrue(
            tuple(print_.mock_calls[0])[1][0].startswith(
                "Unrecognized migration name - must be one of "
            )
        )

    @patch("piccolo.apps.migrations.commands.backwards.print")
    def test_backwards_no_migrations(self, print_: MagicMock):
        """
        Test running migrations backwards if none have been run previously.
        """
        run_sync(
            backwards(
                app_name="music",
                migration_id="2020-12-17T18:44:30",
                auto_agree=True,
            )
        )
        self.assertTrue(
            call("🏁 No migrations to reverse!") in print_.mock_calls
        )

    @patch("piccolo.apps.migrations.commands.forwards.print")
    def test_forwards_no_migrations(self, print_: MagicMock):
        """
        Test running the migrations if they've already run.
        """
        run_sync(forwards(app_name="music", migration_id="all"))
        run_sync(forwards(app_name="music", migration_id="all"))

        self.assertTrue(
            print_.mock_calls[-1] == call("🏁 No migrations need to be run")
        )

    @engines_only("postgres")
    @patch("piccolo.apps.migrations.commands.forwards.input")
    def test_forwards_fake(self, _input: MagicMock):
        """
        Make sure migrations can be faked on the command line.
        """
        _input.return_value = "y"

        run_sync(forwards(app_name="music", migration_id="all", fake=True))

        for table_class in TABLE_CLASSES:
            self.assertTrue(not table_class.table_exists().run_sync())

        ran_migration_names = (
            Migration.select(Migration.name).output(as_list=True).run_sync()
        )

        self.assertListEqual(ran_migration_names, self.get_migration_names())

    @engines_only("postgres")
    @patch("piccolo.apps.migrations.commands.forwards.input")
    def test_forwards_fake_multiple_warns(
        self,
        input_: MagicMock,
    ):
        """
        ``--fake`` marks migrations as run without applying them; when it
        covers several migrations at once it should warn the user.

        https://github.com/piccolo-orm/piccolo/issues/1255
        """
        input_.return_value = "y"
        run_sync(forwards(app_name="music", migration_id="all", fake=True))
        migration_count = len(self.get_migration_names())
        input_.assert_called_once_with(
            f"⚠️ --fake will mark all {migration_count} migrations as run "
            "without applying them. Continue? [y/N]"
        )

    @patch("piccolo.apps.migrations.commands.forwards.print")
    def test_hardcoded_fake_migrations(self, print_: MagicMock):
        """
        Make sure that migrations that have been hardcoded as fake aren't
        executed, even without the ``--fake`` command line flag.

        See tests/example_apps/music/piccolo_migrations/music_2024_06_19t18_11_05_793132.py

        """  # noqa: E501
        run_sync(forwards(app_name="music", migration_id="all"))

        # The migration which is hardcoded as fake:
        migration_name = "2024-06-19T18:11:05:793132"

        self.assertTrue(
            Migration.exists()
            .where(Migration.name == migration_name)
            .run_sync()
        )

        self.assertNotIn(
            call("Running fake migration"),
            print_.mock_calls,
        )
        self.assertIn(
            call(f"  - {migration_name}: faked! ⏭️"),
            print_.mock_calls,
        )

    def tearDown(self):
        for table_class in TABLE_CLASSES + [Migration]:
            table_class.alter().drop_table(
                cascade=True, if_exists=True
            ).run_sync()
