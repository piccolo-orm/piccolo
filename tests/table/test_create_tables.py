from unittest import TestCase

from piccolo.table import create_tables
from tests.example_apps.music.tables import Band, Manager


class TestCreateTables(TestCase):
    def tearDown(self) -> None:
        Band.alter().drop_table(if_exists=True).run_sync()
        Manager.alter().drop_table(if_exists=True).run_sync()

    def test_create_tables(self):
        create_tables(Manager, Band, if_not_exists=False)
        self.assertTrue(Manager.table_exists().run_sync())
        self.assertTrue(Band.table_exists().run_sync())
