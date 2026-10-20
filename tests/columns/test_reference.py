"""
Most of the tests for piccolo/columns/reference.py are covered in
piccolo/columns/test_foreignkey.py
"""

from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.columns.reference import LazyTableReference
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class Band(Table):
    manager: ForeignKey["Manager"] = ForeignKey(
        LazyTableReference("Manager", module_path=__name__)
    )
    name = Varchar()


class Manager(Table):
    name = Varchar()


class TestQueries(TableTest):
    tables = [Band, Manager]

    def setUp(self):
        super().setUp()
        manager = Manager({Manager.name: "Guido"})
        manager.save().run_sync()
        band = Band({Band.name: "Pythonistas", Band.manager: manager})
        band.save().run_sync()

    def test_select(self):
        self.assertListEqual(
            Band.select(Band.name, Band.manager._.name).run_sync(),
            [{"name": "Pythonistas", "manager.name": "Guido"}],
        )


class TestInit(TestCase):
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


class TestStr(TestCase):
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
