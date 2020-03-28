
from unittest import TestCase

from piccolo.migrations.auto.diffable_table import compare_dicts


class TestCompareDicts(TestCase):
    def test_compare_dicts(self):
        dict_1 = {"a": 1, "b": 2}
        dict_2 = {"a": 1, "b": 3}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": 2})
