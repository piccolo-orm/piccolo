import datetime
from unittest import TestCase

from tests.base import engines_only
from tests.example_apps.music.tables import Band


@engines_only("postgres", "cockroach")
class TestArrayPostgres(TestCase):

    def test_string(self):
        self.assertEqual(
            Band.name.get_sql_value(["a", "b", "c"]),
            '\'{"a","b","c"}\'',
        )

    def test_int(self):
        self.assertEqual(
            Band.name.get_sql_value([1, 2, 3]),
            "'{1,2,3}'",
        )

    def test_nested(self):
        self.assertEqual(
            Band.name.get_sql_value([1, 2, 3, [4, 5, 6]]),
            "'{1,2,3,{4,5,6}}'",
        )

    def test_time(self):
        self.assertEqual(
            Band.name.get_sql_value([datetime.time(hour=8, minute=0)]),
            "'{\"08:00:00\"}'",
        )


@engines_only("sqlite")
class TestArraySQLite(TestCase):

    def test_string(self):
        self.assertEqual(
            Band.name.get_sql_value(["a", "b", "c"]),
            '\'["a","b","c"]\'',
        )

    def test_int(self):
        self.assertEqual(
            Band.name.get_sql_value([1, 2, 3]),
            "'[1,2,3]'",
        )

    def test_nested(self):
        self.assertEqual(
            Band.name.get_sql_value([1, 2, 3, [4, 5, 6]]),
            "'[1,2,3,[4,5,6]]'",
        )

    def test_time(self):
        self.assertEqual(
            Band.name.get_sql_value([datetime.time(hour=8, minute=0)]),
            "'[\"08:00:00\"]'",
        )
