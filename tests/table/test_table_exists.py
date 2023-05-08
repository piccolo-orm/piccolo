from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.table import Table
from tests.example_apps.music.tables import Manager


class TestTableExists(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def test_table_exists(self):
        response = Manager.table_exists().run_sync()
        self.assertTrue(response)

    def tearDown(self):
        Manager.alter().drop_table().run_sync()


class Band(Table, schema="schema1"):
    name = Varchar()


class TestTableExistsSchema(TestCase):
    def setUp(self):
        Band.raw("CREATE SCHEMA IF NOT EXISTS 'schema1'")
        Manager.create_table().run_sync()

    def test_table_exists(self):
        """
        Make sure it works correctly if the table is in a Postgres schema.
        """
        response = Manager.table_exists().run_sync()
        self.assertTrue(response)

    def tearDown(self):
        Manager.alter().drop_table().run_sync()
        Band.raw("DROP SCHEMA 'schema1'")
