from __future__ import annotations
from unittest import TestCase
import typing as t

from piccolo.apps.migrations.commands.backwards import backwards
from piccolo.apps.migrations.commands.forwards import forwards

from tests.example_app.tables import (
    Manager,
    Band,
    Venue,
    Concert,
    Ticket,
    Poster,
)

if t.TYPE_CHECKING:
    from piccolo.table import Table


TABLE_CLASSES: t.List[t.Type[Table]] = [
    Manager,
    Band,
    Venue,
    Concert,
    Ticket,
    Poster,
]


class TestForwardsBackwards(TestCase):
    """
    How to test this? Add migrations for the example app, and just run them
    forwards and backwards. Or create a new app with loads of migrations in
    it.
    """

    # TODO - use pytest parameterise ...
    def test_forwards_backwards_all_migrations(self):
        """
        Test running all of the migrations forwards, then backwards.
        """
        forwards(app_name="example_app", migration_id="all")

        # Check the tables exist
        for table_class in TABLE_CLASSES:
            self.assertTrue(table_class.table_exists().run_sync())

        backwards(app_name="example_app", migration_id="all", auto_agree=True)

        # Check the tables don't exist
        for table_class in TABLE_CLASSES:
            self.assertTrue(not table_class.table_exists().run_sync())

    def tearDown(self):
        for table_class in TABLE_CLASSES:
            table_class.alter().drop_table(if_exists=True).run_sync()
