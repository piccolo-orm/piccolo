from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.table import Table, create_tables, drop_tables


class Manager(Table):
    name = Varchar(unique=True)


class Band(Table):
    name = Varchar()
    manager = ForeignKey(Manager, target_column="name")


class TestTargetColumnWithString(TestCase):
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


###############################################################################


class ManagerA(Table):
    name = Varchar(unique=True)


class BandA(Table):
    name = Varchar()
    manager = ForeignKey(ManagerA, target_column=ManagerA.name)


class TestTargetColumnWithColumnRef(TestCase):
    """
    Make sure we can create tables with foreign keys which don't reference
    the primary key.
    """

    def setUp(self):
        create_tables(ManagerA, BandA)

    def tearDown(self):
        drop_tables(ManagerA, BandA)

    def test_queries(self):
        manager_1 = ManagerA.objects().create(name="Guido").run_sync()
        manager_2 = ManagerA.objects().create(name="Graydon").run_sync()

        BandA.insert(
            BandA(name="Pythonistas", manager=manager_1),
            BandA(name="Rustaceans", manager=manager_2),
        ).run_sync()

        response = BandA.select(BandA.name, BandA.manager.name).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "manager.name": "Guido"},
                {"name": "Rustaceans", "manager.name": "Graydon"},
            ],
        )
