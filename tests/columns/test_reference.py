"""
Most of the tests for piccolo/columns/reference.py are covered in
piccolo/columns/test_foreignkey.py
"""
from unittest import TestCase

from piccolo.columns.reference import LazyTableReference


class TestLazyTableReference(TestCase):
    def test_init(self):
        """
        A ``LazyTableReference`` must be passed either an ``app_name`` or
        ``module_path`` argument.
        """
        with self.assertRaises(ValueError):
            LazyTableReference(table_class_name="Manager")

        with self.assertRaises(ValueError):
            LazyTableReference(
                table_class_name="Manager",
                app_name="music",
                module_path="tests.example_apps.music.tables",
            )

        # Shouldn't raise exceptions:
        LazyTableReference(
            table_class_name="Manager",
            app_name="music",
        )
        LazyTableReference(
            table_class_name="Manager",
            module_path="tests.example_apps.music.tables",
        )

    def test_str(self):
        self.assertEqual(
            LazyTableReference(
                table_class_name="Manager",
                app_name="music",
            ).__str__(),
            "App music.Manager",
        )

        self.assertEqual(
            LazyTableReference(
                table_class_name="Manager",
                module_path="tests.example_apps.music.tables",
            ).__str__(),
            "Module tests.example_apps.music.tables.Manager",
        )
