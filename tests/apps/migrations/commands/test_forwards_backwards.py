from __future__ import annotations

import sys
import typing as t
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.migrations.commands.backwards import backwards
from piccolo.apps.migrations.commands.forwards import forwards
from piccolo.apps.migrations.tables import Migration
from piccolo.utils.sync import run_sync
from tests.base import postgres_only
from tests.example_app.tables import (
    Band,
    Concert,
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
]


@postgres_only
class TestForwardsBackwards(TestCase):
    """
    Test the forwards and backwards migration commands.
    """

    def test_forwards_backwards_all_migrations(self):
        """
        Test running all of the migrations forwards, then backwards.
        """
        for app_name in ("example_app", "all"):
            run_sync(forwards(app_name=app_name, migration_id="all"))

            # Check the tables exist
            for table_class in TABLE_CLASSES:
                self.assertTrue(table_class.table_exists().run_sync())

            run_sync(
                backwards(
                    app_name=app_name, migration_id="all", auto_agree=True
                )
            )

            # Check the tables don't exist
            for table_class in TABLE_CLASSES:
                self.assertTrue(not table_class.table_exists().run_sync())

    def test_forwards_backwards_single_migration(self):
        """
        Test running a single migrations forwards, then backwards.
        """
        for migration_id in ["1", "2020-12-17T18:44:30"]:
            run_sync(
                forwards(app_name="example_app", migration_id=migration_id)
            )

            table_classes = [Band, Manager]

            # Check the tables exist
            for table_class in table_classes:
                self.assertTrue(table_class.table_exists().run_sync())

            run_sync(
                backwards(
                    app_name="example_app",
                    migration_id=migration_id,
                    auto_agree=True,
                )
            )

            # Check the tables don't exist
            for table_class in table_classes:
                self.assertTrue(not table_class.table_exists().run_sync())

    @patch("piccolo.apps.migrations.commands.forwards.print")
    def test_forwards_unknown_migration(self, print_: MagicMock):
        """
        Test running an unknown migrations forwards.
        """
        with self.assertRaises(SystemExit):
            run_sync(
                forwards(
                    app_name="example_app", migration_id="migration-12345"
                )
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
        run_sync(forwards(app_name="example_app", migration_id="all"))

        with self.assertRaises(SystemExit):
            run_sync(
                backwards(
                    app_name="example_app",
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
                app_name="example_app",
                migration_id="2020-12-17T18:44:30",
                auto_agree=True,
            )
        )
        self.assertTrue(call("No migrations to reverse!") in print_.mock_calls)

    @patch("piccolo.apps.migrations.commands.forwards.print")
    def test_forwards_no_migrations(self, print_: MagicMock):
        """
        Test running the migrations if they've already run.
        """
        run_sync(forwards(app_name="example_app", migration_id="all"))
        run_sync(forwards(app_name="example_app", migration_id="all"))

        self.assertTrue(
            print_.mock_calls[-1] == call("No migrations left to run!")
        )

    def test_forwards_fake(self):
        """
        Test running the migrations if they've already run.
        """
        run_sync(
            forwards(app_name="example_app", migration_id="all", fake=True)
        )

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
            ],
        )

    def tearDown(self):
        for table_class in TABLE_CLASSES + [Migration]:
            table_class.alter().drop_table(
                cascade=True, if_exists=True
            ).run_sync()
