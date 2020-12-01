from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import JSON


class MyTable(Table):
    json = JSON()


class MyTableDefault(Table):
    """
    Test the different default types.
    """

    json = JSON()
    json_str = JSON(default="{}")
    json_dict = JSON(default={})
    json_list = JSON(default=[])
    json_none = JSON(default=None, null=True)


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


class TestJSONDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_json_default(self):
        row = MyTableDefault()
        row.save().run_sync()

        self.assertEqual(row.json, "{}")
        self.assertEqual(row.json_str, "{}")
        self.assertEqual(row.json_dict, "{}")
        self.assertEqual(row.json_list, "[]")
        self.assertEqual(row.json_none, None)

    def test_invalid_default(self):
        with self.assertRaises(ValueError):
            for value in ("a", 1, ("x", "y", "z")):
                JSON(default=value)
