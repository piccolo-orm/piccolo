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
        self.assertEqual(Manager.table_exists().run_sync(), True)
        self.assertEqual(Band.table_exists().run_sync(), True)

        drop_db_tables_sync(Manager, Band)

        self.assertEqual(Manager.table_exists().run_sync(), False)
        self.assertEqual(Band.table_exists().run_sync(), False)

    def test_drop_tables(self):
        """
        This is a deprecated function, which just acts as a proxy.
        """
        self.assertEqual(Manager.table_exists().run_sync(), True)
        self.assertEqual(Band.table_exists().run_sync(), True)

        drop_tables(Manager, Band)

        self.assertEqual(Manager.table_exists().run_sync(), False)
        self.assertEqual(Band.table_exists().run_sync(), False)
