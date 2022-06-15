from tests.base import DBTestCase
from tests.example_apps.music.tables import Band


class TestRefresh(DBTestCase):
    def setUp(self):
        super().setUp()
        self.insert_rows()

    def test_refresh(self):
        """
        Make sure ``refresh`` works, with not columns specified.
        """
        # Fetch an instance from the database.
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        initial_data = band.to_dict()

        # Modify the data in the database.
        Band.update(
            {Band.name: Band.name + "!!!", Band.popularity: 8000}
        ).where(Band.name == "Pythonistas").run_sync()

        # Refresh `band`, and make sure it has the correct data.
        band.refresh().run_sync()

        self.assertTrue(band.name == "Pythonistas!!!")
        self.assertTrue(band.popularity == 8000)
        self.assertTrue(band.id == initial_data["id"])

    def test_columns(self):
        """
        Make sure ``refresh`` works, when columns are specified.
        """
        # Fetch an instance from the database.
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        initial_data = band.to_dict()

        # Modify the data in the database.
        Band.update(
            {Band.name: Band.name + "!!!", Band.popularity: 8000}
        ).where(Band.name == "Pythonistas").run_sync()

        # Refresh `band`, and make sure it has the correct data.
        query = band.refresh(columns=[Band.name])
        self.assertEqual(
            [i._meta.name for i in query._columns],
            ["name"],
        )
        query.run_sync()

        self.assertTrue(band.name == "Pythonistas!!!")
        self.assertTrue(band.popularity == initial_data["popularity"])
        self.assertTrue(band.id == initial_data["id"])

    def test_error_when_not_in_db(self):
        """
        Make sure we can't refresh an instance which hasn't been saved in the
        database.
        """
        band = Band()

        with self.assertRaises(ValueError) as manager:
            band.refresh().run_sync()

        self.assertEqual(
            "The instance doesn't exist in the database.",
            str(manager.exception),
        )

    def test_error_when_pk_in_none(self):
        """
        Make sure we can't refresh an instance when the primary key value isn't
        set.
        """
        band: Band = Band.objects().first().run_sync()
        band.id = None

        with self.assertRaises(ValueError) as manager:
            band.refresh().run_sync()

        self.assertEqual(
            "The instance's primary key value isn't defined.",
            str(manager.exception),
        )
