from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.table import Table, create_tables, drop_tables


class Manager(Table):
    name = Varchar(unique=True)


class Band(Table):
    name = Varchar()
    manager = ForeignKey(Manager, target_column="name")


class TestTargetColumn(TestCase):
    """
    Make sure we can create tables with foreign keys which don't reference
    the primary key.
    """

    def setUp(self):
        create_tables(Manager, Band)

    def tearDown(self):
        drop_tables(Manager, Band)

    def test_queries(self):
        manager_1 = Manager.objects().create(name="Guido").run_sync()
        manager_2 = Manager.objects().create(name="Graydon").run_sync()

        Band.insert(
            Band(name="Pythonistas", manager=manager_1),
            Band(name="Rustaceans", manager=manager_2),
        ).run_sync()

        response = Band.select(Band.name, Band.manager.name).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "manager.name": "Guido"},
                {"name": "Rustaceans", "manager.name": "Graydon"},
            ],
        )
