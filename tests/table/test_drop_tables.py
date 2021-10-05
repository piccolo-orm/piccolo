from unittest import TestCase

from piccolo.table import create_tables, drop_tables
from tests.example_apps.music.tables import Band, Manager


class TestDropTables(TestCase):
    def setUp(self):
        create_tables(Band, Manager)

    def test_drop_tables(self):
        """
        Make sure the tables are dropped.
        """
        self.assertEqual(Manager.table_exists().run_sync(), True)
        self.assertEqual(Band.table_exists().run_sync(), True)

        drop_tables(Manager, Band)

        self.assertEqual(Manager.table_exists().run_sync(), False)
        self.assertEqual(Band.table_exists().run_sync(), False)
