from unittest import TestCase

from piccolo.table import (
    create_db_tables_sync,
    drop_db_tables_sync,
    drop_tables,
)
from tests.example_apps.music.tables import Band, Manager


class TestDropTables(TestCase):
    def setUp(self):
        create_db_tables_sync(Band, Manager)

    def test_drop_db_tables(self):
        """
        Make sure the tables are dropped.
        """
        self.assertTrue(Manager.table_exists().run_sync())
        self.assertTrue(Band.table_exists().run_sync())

        drop_db_tables_sync(Manager, Band)

        self.assertFalse(Manager.table_exists().run_sync())
        self.assertFalse(Band.table_exists().run_sync())

    def test_drop_tables(self):
        """
        This is a deprecated function, which just acts as a proxy.
        """
        self.assertTrue(Manager.table_exists().run_sync())
        self.assertTrue(Band.table_exists().run_sync())

        drop_tables(Manager, Band)

        self.assertFalse(Manager.table_exists().run_sync())
        self.assertFalse(Band.table_exists().run_sync())
