from unittest import TestCase

from piccolo.table import Table
from piccolo.columns import ForeignKey, Varchar, LazyTableReference


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
        Band2.create_table().run_sync()

    def test_foreign_key_string(self):
        self.assertEqual(
            Band2.manager._foreign_key_meta.resolved_references, Manager
        )

    def tearDown(self):
        Band2.alter().drop_table().run_sync()
        Manager.alter().drop_table().run_sync()


class TestReferences(TestCase):
    def test_foreign_key_references(self):
        """
        Make sure foreign key references are stored correctly on the table
        which is the target of the ForeignKey.
        """
        self.assertEqual(len(Manager._meta.foreign_key_references), 4)

        self.assertTrue(Band1.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band2.manager in Manager._meta.foreign_key_references)
        self.assertTrue(Band3.manager in Manager._meta.foreign_key_references)
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
