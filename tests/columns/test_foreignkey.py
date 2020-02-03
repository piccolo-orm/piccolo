import unittest

from piccolo import columns
from piccolo.table import Table


class Employee(Table):
    name = columns.Varchar()
    manager = columns.ForeignKey("self", null=True)


class TestForeignKeySelf(unittest.TestCase):
    """
    Test that ForeignKey columns can be created with references to the parent
    table.
    """

    def setUp(self):
        Employee.create_table().run_sync()

    def test_readable(self):
        manager = Employee(name="Mr Manager")
        manager.save().run_sync()

        worker = Employee(name="Mr Worker", manager=manager.id)
        worker.save().run_sync()

        response = (
            Employee.select(Employee.name, Employee.manager.name)
            .order_by(Employee.name)
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
        Employee.alter().drop_table().run_sync()
