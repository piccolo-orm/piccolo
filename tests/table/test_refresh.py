import typing as t

from piccolo.testing.test_case import TableTest
from tests.base import DBTestCase
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Manager,
    RecordingStudio,
    Venue,
)


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
        self.assertEqual(band.manager.name, "Guido!!!")

    def test_multiple_layers(self) -> None:
        """
        Make sure ``refresh`` works when ``prefetch`` was used to fetch objects
        multiple layers deep.
        """
        concert = (
            Concert.objects(Concert.band_1._.manager)
            .where(Concert.band_1._.name == "Pythonistas")
            .first()
            .run_sync()
        )
        assert concert is not None

        # Modify the data in the database.
        self.manager.name = "Guido!!!"
        self.manager.save().run_sync()

        concert.refresh().run_sync()
        self.assertEqual(concert.band_1.manager.name, "Guido!!!")

    def test_updated_foreign_key(self) -> None:
        """
        If a foreign key now references a different row, make sure this
        is refreshed correctly.
        """
        band = (
            Band.objects(Band.manager)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        assert band is not None

        # Assign a different manager to the band
        new_manager = Manager({Manager.name: "New Manager"})
        new_manager.save().run_sync()
        Band.update({Band.manager: new_manager.id}, force=True).run_sync()

        # Refresh `band`, and make sure it references the new manager.
        band.refresh().run_sync()
        self.assertEqual(band.manager.id, new_manager.id)
        self.assertEqual(band.manager.name, "New Manager")

    def test_foreign_key_set_to_null(self):
        """
        Make sure that if the foreign key was set to null, that ``refresh``
        sets the nested object to ``None``.
        """
        band = (
            Band.objects(Band.manager)
            .where(Band.name == "Pythonistas")
            .first()
            .run_sync()
        )
        assert band is not None

        # Remove the manager from band
        Band.update({Band.manager: None}, force=True).run_sync()

        # Refresh `band`, and make sure the foreign key value is now `None`,
        # instead of a nested object.
        band.refresh().run_sync()
        self.assertIsNone(band.manager)

    def test_exception(self) -> None:
        """
        We don't currently let the user refresh specific fields from nested
        objects - an exception should be raised.
        """
        with self.assertRaises(ValueError):
            self.concert.refresh(columns=[Concert.band_1._.manager]).run_sync()

        # Shouldn't raise an exception:
        self.concert.refresh(columns=[Concert.band_1]).run_sync()


class TestRefreshWithLoadJSON(TableTest):

    tables = [RecordingStudio]

    def setUp(self):
        super().setUp()

        self.recording_studio = RecordingStudio(
            {RecordingStudio.facilities: {"piano": True}}
        )
        self.recording_studio.save().run_sync()

    def test_load_json(self):
        """
        Make sure we can refresh an object, and load the JSON as a Python
        object.
        """
        RecordingStudio.update(
            {RecordingStudio.facilities: {"electric piano": True}},
            force=True,
        ).run_sync()

        # Refresh without load_json:
        self.recording_studio.refresh().run_sync()

        self.assertEqual(
            # Remove the white space, because some versions of Python add
            # whitespace around JSON, and some don't.
            self.recording_studio.facilities.replace(" ", ""),
            '{"electricpiano":true}',
        )

        # Refresh with load_json:
        self.recording_studio.refresh(load_json=True).run_sync()

        self.assertDictEqual(
            t.cast(dict, self.recording_studio.facilities),
            {"electric piano": True},
        )
