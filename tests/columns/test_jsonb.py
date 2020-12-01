from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import JSONB

from ..base import postgres_only


class MyTable(Table):
    json = JSONB()


@postgres_only
class TestJSON(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_json(self):
        """
        Test storing a valid JSON string.
        """
        row = MyTable(json='{"a": 1}')
        row.save().run_sync()
        self.assertEqual(row.json, '{"a": 1}')

    def test_arrow(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        MyTable(json='{"a": 1}').save().run_sync()
        row = MyTable.select(MyTable.json.arrow("a")).first().run_sync()
        self.assertEqual(row["json"], "1")
