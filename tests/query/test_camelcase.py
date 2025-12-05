from unittest import TestCase

from piccolo.columns import ForeignKey, Varchar
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync


class Manager(Table):
    theName = Varchar()


class Band(Table):
    theName = Varchar()
    theManager = ForeignKey(Manager)


class TestCamelCase(TestCase):
    def setUp(self):
        create_db_tables_sync(Manager, Band)

    def tearDown(self):
        drop_db_tables_sync(Manager, Band)

    def test_queries(self):
        """
        Make sure that basic queries work when the columns use camelCase.
        """
        manager_names = ("Guido", "Maz", "Graydon")
        band_names = ("Pythonistas", "Rubyists", "Rustaceans")

        # Test create
        for manager_name, band_name in zip(manager_names, band_names):
            manager = Manager.objects().create(theName=manager_name).run_sync()
            Band.objects().create(
                theName=band_name, theManager=manager
            ).run_sync()

        # Test select, with joins
        response = (
            Band.select(
                Band.theName,
                Band.theManager.theName.as_alias("theManagerName"),
            )
            .order_by(Band.theName)
            .run_sync()
        )
        self.assertListEqual(
            response,
            [
                {"theName": "Pythonistas", "theManagerName": "Guido"},
                {"theName": "Rubyists", "theManagerName": "Maz"},
                {"theName": "Rustaceans", "theManagerName": "Graydon"},
            ],
        )

        # Test delete
        Band.delete().where(Band.theName == "Rubyists").run_sync()

        # Test exists
        self.assertFalse(
            Band.exists().where(Band.theName == "Rubyists").run_sync()
        )
