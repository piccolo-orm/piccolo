from unittest import TestCase
import time

from piccolo.table import Table
from piccolo.columns import Column, ForeignKey, Varchar, LazyTableReference


class Manager(Table):
    name = Varchar()
    manager = ForeignKey("self", null=True)


class Band1(Table):
    manager = ForeignKey(references=Manager)


class Band2(Table):
    manager = ForeignKey(references="Manager")


class Band3(Table):
    manager = ForeignKey(
        references=LazyTableReference(
            table_class_name="Manager",
            module_path="tests.columns.test_foreignkey",
        )
    )


class Band4(Table):
    manager = ForeignKey(references="tests.columns.test_foreignkey.Manager")


class TestForeignKeySelf(TestCase):
    """
    Test that ForeignKey columns can be created with references to the parent
    table.
    """

    def setUp(self):
        Manager.create_table().run_sync()

    def test_foreign_key_self(self):
        manager = Manager(name="Mr Manager")
        manager.save().run_sync()

        worker = Manager(name="Mr Worker", manager=manager.id)
        worker.save().run_sync()

        response = (
            Manager.select(Manager.name, Manager.manager.name)
            .order_by(Manager.name)
            .run_sync()
        )
        self.assertEqual(
            response,
            [
                {"name": "Mr Manager", "manager.name": None},
                {"name": "Mr Worker", "manager.name": "Mr Manager"},
            ],
        )

    def tearDown(self):
        Manager.alter().drop_table().run_sync()


class TestForeignKeyString(TestCase):
    """
    Test that ForeignKey columns can be created with a `references` argument
    set as a string value.
    """

    def setUp(self):
        Manager.create_table().run_sync()

    def test_foreign_key_string(self):
        Band2.create_table().run_sync()
        self.assertEqual(
            Band2.manager._foreign_key_meta.resolved_references, Manager
        )
        Band2.alter().drop_table().run_sync()

        Band4.create_table().run_sync()
        self.assertEqual(
            Band4.manager._foreign_key_meta.resolved_references, Manager
        )
        Band4.alter().drop_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()


class TestForeignKeyRelativeError(TestCase):
    def test_foreign_key_relative_error(self):
        """
        Make sure that a references argument which contains a relative module
        isn't allowed.
        """
        with self.assertRaises(ValueError) as manager:

            class Band(Table):
                manager = ForeignKey("..example_app.tables.Manager", null=True)

        self.assertEqual(
            manager.exception.__str__(), "Relative imports aren't allowed"
        )


class TestReferences(TestCase):
    def test_foreign_key_references(self):
        """
        Make sure foreign key references are stored correctly on the table
        which is the target of the ForeignKey.
        """
        self.assertEqual(len(Manager._meta.foreign_key_references), 5)

        self.assertTrue(Band1.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band2.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band3.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band4.manager in Manager._meta.foreign_key_references)
        self.assertTrue(
            Manager.manager in Manager._meta.foreign_key_references
        )


class TestLazyTableReference(TestCase):
    def test_lazy_reference_to_app(self):
        """
        Make sure a LazyTableReference to a Table within a Piccolo app works.
        """
        from tests.example_app.tables import Manager

        reference = LazyTableReference(
            table_class_name="Manager", app_name="example_app"
        )
        self.assertTrue(reference.resolve() is Manager)


class TestAttributeAccess(TestCase):
    def test_attribute_access(self):
        """
        Make sure that attribute access still works correctly with lazy
        references.
        """
        self.assertTrue(isinstance(Band1.manager.name, Varchar))
        self.assertTrue(isinstance(Band2.manager.name, Varchar))
        self.assertTrue(isinstance(Band3.manager.name, Varchar))
        self.assertTrue(isinstance(Band4.manager.name, Varchar))

    def test_recursion_limit(self):
        """
        When a table has a ForeignKey to itself, an Exception should be raised
        if the call chain is too large.
        """
        # Should be fine:
        column: Column = Manager.manager.name
        self.assertTrue(len(column._meta.call_chain), 1)
        self.assertTrue(isinstance(column, Varchar))

        with self.assertRaises(Exception):
            Manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.manager.name  # noqa

    def test_recursion_time(self):
        """
        Make sure that a really large call chain doesn't take too long.
        """
        start = time.time()
        Manager.manager.manager.manager.manager.manager.manager.name
        end = time.time()
        self.assertTrue(end - start < 1.0)
