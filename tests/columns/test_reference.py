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
                app_name="example_app",
                module_path="tests.example_app.tables",
            )

        # Shouldn't raise exceptions:
        LazyTableReference(
            table_class_name="Manager",
            app_name="example_app",
        )
        LazyTableReference(
            table_class_name="Manager",
            module_path="tests.example_app.tables",
        )

    def test_str(self):
        self.assertEqual(
            LazyTableReference(
                table_class_name="Manager",
                app_name="example_app",
            ).__str__(),
            "App example_app.Manager",
        )

        self.assertEqual(
            LazyTableReference(
                table_class_name="Manager",
                module_path="tests.example_app.tables",
            ).__str__(),
            "Module tests.example_app.tables.Manager",
        )
