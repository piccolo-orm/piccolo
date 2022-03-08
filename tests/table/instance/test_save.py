from unittest import TestCase

from piccolo.table import create_tables, drop_tables
from tests.example_apps.music.tables import Band, Manager


class TestSave(TestCase):
    def setUp(self):
        create_tables(Manager, Band)

    def tearDown(self):
        drop_tables(Manager, Band)

    def test_save_new(self):
        """
        Make sure that saving a new instance works.
        """
        manager = Manager(name="Maz")

        query = manager.save()
        print(query)
        self.assertTrue("INSERT" in query.__str__())

        query.run_sync()

        names = [i["name"] for i in Manager.select(Manager.name).run_sync()]
        self.assertTrue("Maz" in names)

        manager.name = "Maz2"
        query = manager.save()
        print(query)
        self.assertTrue("UPDATE" in query.__str__())

        query.run_sync()
        names = [i["name"] for i in Manager.select(Manager.name).run_sync()]
        self.assertTrue("Maz2" in names)
        self.assertTrue("Maz" not in names)

    def test_save_specific_columns(self):
        """
        Make sure that we can save a subset of columns.
        """
        manager = Manager(name="Guido")
        manager.save().run_sync()

        band = Band(name="Pythonistas", popularity=1000, manager=manager)
        band.save().run_sync()

        self.assertEqual(
            Band.select().run_sync(),
            [
                {
                    "id": 1,
                    "name": "Pythonistas",
                    "manager": 1,
                    "popularity": 1000,
                }
            ],
        )

        band.name = "Pythonistas 2"
        band.popularity = 2000
        band.save(columns=[Band.name]).run_sync()

        # Only the name should update, and not the popularity:
        self.assertEqual(
            Band.select().run_sync(),
            [
                {
                    "id": 1,
                    "name": "Pythonistas 2",
                    "manager": 1,
                    "popularity": 1000,
                }
            ],
        )

        #######################################################################

        # Also test it using strings to identify columns
        band.name = "Pythonistas 3"
        band.popularity = 3000
        band.save(columns=["popularity"]).run_sync()

        # Only the popularity should update, and not the name:
        self.assertEqual(
            Band.select().run_sync(),
            [
                {
                    "id": 1,
                    "name": "Pythonistas 2",
                    "manager": 1,
                    "popularity": 3000,
                }
            ],
        )
