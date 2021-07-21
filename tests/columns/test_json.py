from unittest import TestCase

from piccolo.columns.column_types import JSON
from piccolo.table import Table


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


class TestJSONSave(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_json_string(self):
        """
        Test storing a valid JSON string.
        """
        row = MyTable(json='{"a": 1}')
        row.save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.json)
            .first()
            .run_sync()["json"]
            .replace(" ", ""),
            '{"a":1}',
        )

    def test_json_object(self):
        """
        Test storing a valid JSON object.
        """
        row = MyTable(json={"a": 1})
        row.save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.json)
            .first()
            .run_sync()["json"]
            .replace(" ", ""),
            '{"a":1}',
        )


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


class TestJSONInsert(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def check_response(self):
        self.assertEqual(
            MyTable.select(MyTable.json)
            .first()
            .run_sync()["json"]
            .replace(" ", ""),
            '{"message":"original"}',
        )

    def test_json_string(self):
        """
        Test inserting using a string.
        """
        row = MyTable(json='{"message": "original"}')
        MyTable.insert(row).run_sync()
        self.check_response()

    def test_json_object(self):
        """
        Test inserting using an object.
        """
        row = MyTable(json={"message": "original"})
        MyTable.insert(row).run_sync()


class TestJSONUpdate(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def add_row(self):
        row = MyTable(json={"message": "original"})
        row.save().run_sync()

    def check_response(self):
        self.assertEqual(
            MyTable.select(MyTable.json)
            .first()
            .run_sync()["json"]
            .replace(" ", ""),
            '{"message":"updated"}',
        )

    def test_json_update_string(self):
        """
        Test updating a JSON field using a string.
        """
        self.add_row()
        MyTable.update({MyTable.json: '{"message": "updated"}'}).run_sync()
        self.check_response()

    def test_json_update_object(self):
        """
        Test updating a JSON field using an object.
        """
        self.add_row()
        MyTable.update({MyTable.json: {"message": "updated"}}).run_sync()
        self.check_response()
