from tests.base import DBTestCase, TableTest
from tests.example_apps.music.tables import Band, Concert, Manager, Venue


class TestRefresh(DBTestCase):
    def setUp(self):
        super().setUp()
        self.insert_rows()

    def test_refresh(self) -> None:
        """
        Make sure ``refresh`` works, with no columns specified.
        """
        # Fetch an instance from the database.
        band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        assert band is not None
        initial_data = band.to_dict()

        # Modify the data in the database.
        Band.update(
            {Band.name: Band.name + "!!!", Band.popularity: 8000}
        ).where(Band.name == "Pythonistas").run_sync()

        # Refresh `band`, and make sure it has the correct data.
        band.refresh().run_sync()

        self.assertEqual(band.name, "Pythonistas!!!")
        self.assertEqual(band.popularity, 8000)
        self.assertEqual(band.id, initial_data["id"])

    def test_refresh_with_prefetch(self) -> None:
        """
        Make sure ``refresh`` works, when the object used prefetch to get
        nested objets (the nested objects should be updated too).
        """
        band = (
            Band.objects(Band.manager)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        assert band is not None

        # Modify the data in the database.
        Manager.update({Manager.name: "Guido!!!"}).where(
            Manager.name == "Guido"
        ).run_sync()

        # Refresh `band`, and make sure it has the correct data.
        band.refresh().run_sync()

        self.assertEqual(band.manager.name, "Guido!!!")

    def test_refresh_with_prefetch_multiple_layers_deep(self) -> None:
        """
        Make sure ``refresh`` works, when the object used prefetch to get
        nested objets (the nested objects should be updated too).
        """
        band = (
            Band.objects(Band.manager)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        assert band is not None

        # Modify the data in the database.
        Manager.update({Manager.name: "Guido!!!"}).where(
            Manager.name == "Guido"
        ).run_sync()

        # Refresh `band`, and make sure it has the correct data.
        band.refresh().run_sync()

        self.assertEqual(band.manager.name, "Guido!!!")

    def test_columns(self) -> None:
        """
        Make sure ``refresh`` works, when columns are specified.
        """
        # Fetch an instance from the database.
        band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        assert band is not None
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

        self.assertEqual(band.name, "Pythonistas!!!")
        self.assertEqual(band.popularity, initial_data["popularity"])
        self.assertEqual(band.id, initial_data["id"])

    def test_error_when_not_in_db(self) -> None:
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

    def test_error_when_pk_in_none(self) -> None:
        """
        Make sure we can't refresh an instance when the primary key value isn't
        set.
        """
        band = Band.objects().first().run_sync()
        assert band is not None
        band.id = None

        with self.assertRaises(ValueError) as manager:
            band.refresh().run_sync()

        self.assertEqual(
            "The instance's primary key value isn't defined.",
            str(manager.exception),
        )


class TestRefreshWithPrefetch(TableTest):

    tables = [Manager, Band, Concert, Venue]

    def setUp(self):
        super().setUp()

        self.manager = Manager({Manager.name: "Guido"})
        self.manager.save().run_sync()

        self.band = Band(
            {Band.name: "Pythonistas", Band.manager: self.manager}
        )
        self.band.save().run_sync()

        self.concert = Concert({Concert.band_1: self.band})
        self.concert.save().run_sync()

    def test_single_layer(self) -> None:
        """
        Make sure ``refresh`` works, when the object used prefetch to get
        nested objects (the nested objects should be updated too).
        """
        band = (
            Band.objects(Band.manager)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        assert band is not None

        # Modify the data in the database.
        self.manager.name = "Guido!!!"
        self.manager.save().run_sync()

        # Refresh `band`, and make sure it has the correct data.
        band.refresh().run_sync()
        self.assertEqual(self.band.manager.name, "Guido!!!")

    def test_multiple_layers(self) -> None:
        """
        Make sure ``refresh`` works when ``prefetch`` was used to fetch objects
        multiple layers deep.
        """
        concert = (
            Concert.objects(Concert.band_1._.manager)
            .where(Concert.band_1._.name == "Pythonistas")
            .first()
        )
        assert concert is not None

        # Modify the data in the database.
        self.manager.name = "Guido!!!"
        self.manager.save().run_sync()

        self.concert.refresh().run_sync()
        self.assertEqual(self.concert.band_1.manager.name, "Guido!!!")

    def test_exception(self) -> None:
        """
        We don't currently let the user refresh specific fields from nested
        objects - an exception should be raised.
        """
        with self.assertRaises(ValueError):
            self.concert.refresh(columns=[Concert.band_1._.manager]).run_sync()

        # Shouldn't raise an exception:
        self.concert.refresh(columns=[Concert.band_1]).run_sync()
