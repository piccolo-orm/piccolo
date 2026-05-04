import time
from enum import Enum
from unittest import TestCase

import pytest

from piccolo.columns.column_types import JSON, JSONB, Array, Integer, Varchar
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
            convert_to_sql_value(
                value=instance, column=MyTable._meta.primary_key
            ),
            1,
        )

    def test_convert_enum(self):
        """
        Make sure Enum instances are converted to their values.
        """

        class Colour(Enum):
            red = "r"

        self.assertEqual(
            convert_to_sql_value(value=Colour.red, column=Varchar()), "r"
        )

    def test_other(self):
        """
        Make sure simple Python values are returned correctly.
        """
        self.assertEqual(
            convert_to_sql_value(value=1, column=Integer()),
            1,
        )

    def test_convert_enum_list(self):
        """
        It's possible to have a list of enums when using ``Array`` columns.
        """

        class Colour(Enum):
            red = "r"
            green = "g"
            blue = "b"

        self.assertEqual(
            convert_to_sql_value(
                value=[Colour.red, Colour.green, Colour.blue],
                column=Array(Varchar()),
            ),
            ["r", "g", "b"],
        )

    @pytest.mark.speed
    def test_convert_large_list(self):
        """
        Large lists are problematic. We need to check each value in the list,
        but as efficiently as possible.
        """
        start = time.time()

        convert_to_sql_value(
            value=[i for i in range(1000)],
            column=Array(Varchar()),
        )

        duration = time.time() - start
        print(duration)
