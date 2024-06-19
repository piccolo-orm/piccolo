from __future__ import annotations

import sys
import typing as t
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.migrations.commands.backwards import backwards
from piccolo.apps.migrations.commands.forwards import forwards
from piccolo.apps.migrations.tables import Migration
from piccolo.utils.sync import run_sync
from tests.base import engines_only
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Instrument,
    Manager,
    Poster,
    RecordingStudio,
    Shirt,
    Ticket,
    Venue,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table

TABLE_CLASSES: t.List[t.Type[Table]] = [
    Manager,
    Band,
    Venue,
    Concert,
    Ticket,
    Poster,
    Shirt,
    RecordingStudio,
    Instrument,
]


@engines_only("postgres", "cockroach")
class TestForwardsBackwards(TestCase):
    """
    Test the forwards and backwards migration commands.
    """

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
    def test_forwards_fake(self):
        """
        Make sure migrations can be faked on the command line.
        """
        run_sync(forwards(app_name="music", migration_id="all", fake=True))

        for table_class in TABLE_CLASSES:
            self.assertTrue(not table_class.table_exists().run_sync())

        ran_migration_names = (
            Migration.select(Migration.name).output(as_list=True).run_sync()
        )

        self.assertEqual(
            ran_migration_names,
            # TODO - rather than hardcoding, might fetch these dynamically.
            [
                "2020-12-17T18:44:30",
                "2020-12-17T18:44:39",
                "2020-12-17T18:44:44",
                "2021-07-25T22:38:48:009306",
                "2021-09-06T13:58:23:024723",
                "2021-11-13T14:01:46:114725",
                "2024-05-28T23:15:41:018844",
                "2024-06-19T18:11:05:793132",
            ],
        )

    @engines_only("postgres")
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
            call(f"- {migration_name}: faked! ⏭️"),
            print_.mock_calls,
        )

    def tearDown(self):
        for table_class in TABLE_CLASSES + [Migration]:
            table_class.alter().drop_table(
                cascade=True, if_exists=True
            ).run_sync()
