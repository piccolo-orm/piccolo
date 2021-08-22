from unittest import TestCase

from piccolo.apps.migrations.auto.diffable_table import (
    DiffableTable,
    compare_dicts,
)
from piccolo.columns import OnDelete, Varchar


class TestCompareDicts(TestCase):
    def test_simple(self):
        """
        Make sure that simple values are compared properly.
        """
        dict_1 = {"a": 1, "b": 2}
        dict_2 = {"a": 1, "b": 3}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": 2})

    def test_missing_keys(self):
        """
        Make sure that if one dictionary has keys that the other doesn't,
        it works as expected.
        """
        dict_1 = {"a": 1}
        dict_2 = {"b": 2, "c": 3}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"a": 1})

    def test_list_value(self):
        """
        Make sure list values work correctly.
        """
        dict_1 = {"a": 1, "b": [1]}
        dict_2 = {"a": 1, "b": [2]}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": [1]})

    def test_dict_value(self):
        """
        Make sure dictionary values work correctly.
        """
        dict_1 = {"a": 1, "b": {"x": 1}}
        dict_2 = {"a": 1, "b": {"x": 1}}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {})

        dict_1 = {"a": 1, "b": {"x": 1}}
        dict_2 = {"a": 1, "b": {"x": 2}}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": {"x": 1}})

    def test_none_values(self):
        """
        Make sure there are no edge cases when using None values.
        """
        dict_1 = {"a": None, "b": 1}
        dict_2 = {"a": None}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": 1})

    def test_enum_values(self):
        """
        Make sure Enum values can be compared correctly.
        """
        dict_1 = {"a": OnDelete.cascade}
        dict_2 = {"a": OnDelete.cascade}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {})

        dict_1 = {"a": OnDelete.set_default}
        dict_2 = {"a": OnDelete.cascade}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"a": OnDelete.set_default})


class TestDiffableTable(TestCase):
    def test_subtract(self):
        kwargs = {"class_name": "Manager", "tablename": "manager"}

        name_column_1 = Varchar(unique=False)
        name_column_1._meta.name = "name"
        table_1 = DiffableTable(**kwargs, columns=[name_column_1])

        name_column_2 = Varchar(unique=True)
        name_column_2._meta.name = "name"
        table_2 = DiffableTable(**kwargs, columns=[name_column_2])

        delta = table_2 - table_1

        self.assertEqual(delta.alter_columns[0].params, {"unique": True})
        self.assertEqual(delta.alter_columns[0].old_params, {"unique": False})
