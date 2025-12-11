from piccolo.columns.column_types import JSON
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_only


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


class TestJSONSave(TableTest):
    tables = [MyTable]

    def test_json_string(self):
        """
        Test storing a valid JSON string.
        """
        row = MyTable(json='{"a": 1}')
        row.save().run_sync()

        row_from_db = MyTable.select(MyTable.json).first().run_sync()
        assert row_from_db is not None

        self.assertEqual(
            row_from_db["json"].replace(" ", ""),
            '{"a":1}',
        )

    def test_json_object(self):
        """
        Test storing a valid JSON object.
        """
        row = MyTable(json={"a": 1})
        row.save().run_sync()

        row_from_db = MyTable.select(MyTable.json).first().run_sync()
        assert row_from_db is not None

        self.assertEqual(
            row_from_db["json"].replace(" ", ""),
            '{"a":1}',
        )


class TestJSONDefault(TableTest):
    tables = [MyTableDefault]

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
                JSON(default=value)  # type: ignore


class TestJSONInsert(TableTest):
    tables = [MyTable]

    def check_response(self):
        row = MyTable.select(MyTable.json).first().run_sync()
        assert row is not None
        self.assertEqual(
            row["json"].replace(" ", ""),
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


class TestJSONUpdate(TableTest):
    tables = [MyTable]

    def add_row(self):
        row = MyTable(json={"message": "original"})
        row.save().run_sync()

    def check_response(self):
        row = MyTable.select(MyTable.json).first().run_sync()
        assert row is not None
        self.assertEqual(
            row["json"].replace(" ", ""),
            '{"message":"updated"}',
        )

    def test_json_update_string(self):
        """
        Test updating a JSON field using a string.
        """
        self.add_row()
        MyTable.update(
            {MyTable.json: '{"message": "updated"}'}, force=True
        ).run_sync()
        self.check_response()

    def test_json_update_object(self):
        """
        Test updating a JSON field using an object.
        """
        self.add_row()
        MyTable.update(
            {MyTable.json: {"message": "updated"}}, force=True
        ).run_sync()
        self.check_response()


@engines_only("mysql")
class TestJSONFunctionMySQL(TableTest):
    tables = [MyTable]

    def add_row(self):
        row = MyTable(json={"message": "original"})
        row.save().run_sync()

    def test_from_path_mysql(self):
        """
        Make sure ``from_path`` can be used for complex nested data.
        """
        MyTable(
            json={
                "message": [
                    {"name": "original"},
                    {"name": "copy"},
                ]
            },
        ).save().run_sync()

        response = (
            MyTable.select(
                MyTable.json.from_path(["$.message[0].name"]).as_alias(
                    "message_alias"
                )
            )
            .output(load_json=True)
            .run_sync()
        )

        assert response is not None
        self.assertListEqual(response, [{"message_alias": "original"}])

    def test_arrow_mysql(self):
        """
        Test using the arrow function to retrieve a subset of the JSON.
        """
        MyTable(json={"name": "original"}).save().run_sync()

        response = (
            MyTable.select(MyTable.json.arrow("$.name"))
            .output(load_json=True)
            .first()
            .run_sync()
        )

        assert response is not None
        self.assertEqual(response["json"], "original")

    def test_arrow_as_alias_mysql(self):
        """
        Test using the arrow function with alias.
        """
        MyTable(json={"name": "original"}).save().run_sync()

        response = (
            MyTable.select(MyTable.json.arrow("$.name").as_alias("alias_name"))
            .output(load_json=True)
            .first()
            .run_sync()
        )

        assert response is not None
        self.assertEqual(response["alias_name"], "original")

    def test_square_brackets_mysql(self):
        """
        Make sure we can use square brackets instead of calling ``arrow``
        explicitly.
        """
        MyTable(json={"name": "original"}).save().run_sync()

        response = (
            MyTable.select(MyTable.json["$.name"])
            .output(load_json=True)
            .first()
            .run_sync()
        )

        assert response is not None
        self.assertEqual(response["json"], "original")

    def test_multiple_levels_deep_square_brackets_mysql(self):
        """
        Make sure elements can be extracted multiple levels deep using
        square brackets, not arrow functions
        """
        MyTable(
            json={
                "message": [
                    {"name": "original"},
                    {"name": "copy"},
                ]
            },
        ).save().run_sync()

        response = (
            MyTable.select(
                MyTable.json["$.message[0].name"].as_alias("message_alias")
            )
            .output(load_json=True)
            .run_sync()
        )

        assert response is not None
        self.assertListEqual(response, [{"message_alias": "original"}])

    def test_arrow_where_mysql(self):
        """
        Make sure the arrow function can be used within a WHERE clause.
        """
        MyTable(json={"name": "original"}).save().run_sync()

        self.assertEqual(
            MyTable.count()
            .where(MyTable.json.arrow("$.name").eq("original"))
            .run_sync(),
            1,
        )

        self.assertEqual(
            MyTable.count()
            .where(MyTable.json.arrow("$.name").eq("copy"))
            .run_sync(),
            0,
        )
