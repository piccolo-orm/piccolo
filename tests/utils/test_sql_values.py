from unittest import TestCase

from piccolo.columns.column_types import Integer, JSON, JSONB
from piccolo.table import Table
from piccolo.utils.sql_values import convert_to_sql_value


class TestConvertToSQLValue(TestCase):
    def test_convert_json(self):
        """
        Make sure Python objects are serialised correctly to JSON strings.
        """
        self.assertEqual(
            convert_to_sql_value(value={"a": 123}, column=JSON()).replace(
                " ", ""
            ),
            '{"a":123}',
        )

        self.assertEqual(
            convert_to_sql_value(value={"a": 123}, column=JSONB()).replace(
                " ", ""
            ),
            '{"a":123}',
        )

    def test_convert_table_instance(self):
        """
        Make sure Table instances are converted to integers.
        """

        class MyTable(Table):
            pass

        instance = MyTable(id=1)

        self.assertEqual(
            convert_to_sql_value(value=instance, column=MyTable.id), 1
        )

    def test_other(self):
        """
        Make sure simple Python values are returned correctly.
        """
        self.assertEqual(
            convert_to_sql_value(value=1, column=Integer()), 1,
        )

