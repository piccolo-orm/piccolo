from unittest import TestCase

from piccolo.columns import Varchar
from piccolo.schema import SchemaManager
from piccolo.table import Table
from tests.base import engines_skip
from tests.example_apps.music.tables import Manager


class TestTableExists(TestCase):
    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

    def test_table_exists(self):
        response = Manager.table_exists().run_sync()
        self.assertTrue(response)


class Band(Table, schema="schema_1"):
    name = Varchar()


@engines_skip("sqlite")
class TestTableExistsSchema(TestCase):
    def setUp(self):
        Band.create_table(auto_create_schema=True).run_sync()

    def tearDown(self):
        SchemaManager().drop_schema(
            "schema_1", if_exists=True, cascade=True
        ).run_sync()

    def test_table_exists(self):
        """
        Make sure it works correctly if the table is in a Postgres schema.
        """
        response = Band.table_exists().run_sync()
        self.assertTrue(response)
