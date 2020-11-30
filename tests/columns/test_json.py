from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import JSON


class MyTable(Table):
    json = JSON()


class MyTableDefault(Table):
    json = JSON(default="{}")


class TestJSON(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_json(self):
        row = MyTable(json='{"a": 1}')
        row.save().run_sync()
        self.assertEqual(row.json, '{"a": 1}')

    def test_json_default(self):
        row = MyTable()
        row.save().run_sync()
        self.assertEqual(row.json, "{}")
