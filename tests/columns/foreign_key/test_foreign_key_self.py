from unittest import TestCase

from piccolo.columns import ForeignKey, Serial, Varchar
from piccolo.table import Table


class Manager(Table, tablename="manager"):
    id: Serial
    name = Varchar()
    manager: ForeignKey["Manager"] = ForeignKey("self", null=True)


class TestForeignKeySelf(TestCase):
    """
    Test that ForeignKey columns can be created with references to the parent
    table.
    """

    def setUp(self):
        Manager.create_table().run_sync()

    def tearDown(self):
        Manager.alter().drop_table().run_sync()

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
