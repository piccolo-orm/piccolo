from unittest import TestCase

from piccolo.table import (
    create_db_tables_sync,
    create_tables,
    drop_db_tables_sync,
)
from tests.example_apps.music.tables import Band, Manager


class TestCreateDBTables(TestCase):
    def tearDown(self) -> None:
        drop_db_tables_sync(Manager, Band)

    def test_create_db_tables(self):
        """
        Make sure the tables are created in the database.
        """
        create_db_tables_sync(Manager, Band, if_not_exists=False)
        self.assertTrue(Manager.table_exists().run_sync())
        self.assertTrue(Band.table_exists().run_sync())

    def test_create_tables(self):
        """
        This is a deprecated function, which just acts as a proxy.
        """
        create_tables(Manager, Band, if_not_exists=False)
        self.assertTrue(Manager.table_exists().run_sync())
        self.assertTrue(Band.table_exists().run_sync())
