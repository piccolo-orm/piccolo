
from unittest import TestCase

from piccolo.apps.migrations.auto.diffable_table import (
    compare_dicts,
    DiffableTable
)
from piccolo.columns import Varchar


class TestCompareDicts(TestCase):
    def test_compare_dicts(self):
        dict_1 = {"a": 1, "b": 2}
        dict_2 = {"a": 1, "b": 3}
        response = compare_dicts(dict_1, dict_2)
        self.assertEqual(response, {"b": 2})


class TestDiffableTable(TestCase):
    def test_subtract(self):
        kwargs = {
            'class_name': "Manager",
            'tablename': 'manager'
        }

        name_column_1 = Varchar(unique=False)
        name_column_1._meta.name = "name"
        table_1 = DiffableTable(
            **kwargs,
            columns=[name_column_1]
        )

        name_column_2 = Varchar(unique=True)
        name_column_2._meta.name = "name"
        table_2 = DiffableTable(
            **kwargs,
            columns=[name_column_2]
        )

        delta = table_1 - table_2

        self.assertEqual(
            delta.alter_columns[0].params, {'unique': True}
        )
        self.assertEqual(
            delta.alter_columns[0].old_params, {'unique': False}
        )
