from unittest import TestCase

from piccolo.columns.column_types import JSONB
from piccolo.table import Table

from ..base import postgres_only


class MyTable(Table):
    json = JSONB()


@postgres_only
class TestJSONB(TestCase):
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
        self.assertEqual(row["?column?"], "1")

    def test_arrow_as_alias(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        MyTable(json='{"a": 1}').save().run_sync()
        row = (
            MyTable.select(MyTable.json.arrow("a").as_alias("a"))
            .first()
            .run_sync()
        )
        self.assertEqual(row["a"], "1")

    def test_arrow_where(self):
        """
        Make sure the arrow function can be used within a WHERE clause.
        """
        MyTable(json='{"a": 1}').save().run_sync()
        self.assertEqual(
            MyTable.count().where(MyTable.json.arrow("a") == "1").run_sync(), 1
        )

        self.assertEqual(
            MyTable.count().where(MyTable.json.arrow("a") == "2").run_sync(), 0
        )

    def test_arrow_first(self):
        """
        Make sure the arrow function can be used with the first clause.
        """
        MyTable.insert(
            MyTable(json='{"a": 1}'),
            MyTable(json='{"b": 2}'),
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.json.arrow("a").as_alias("json"))
            .first()
            .run_sync(),
            {"json": "1"},
        )
