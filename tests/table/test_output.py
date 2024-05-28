import json
from unittest import TestCase

from piccolo.table import create_db_tables_sync, drop_db_tables_sync
from tests.base import DBTestCase
from tests.example_apps.music.tables import Band, Instrument, RecordingStudio


class TestOutputList(DBTestCase):
    def test_output_as_list(self):
        self.insert_row()

        response = Band.select(Band.name).output(as_list=True).run_sync()
        self.assertEqual(response, ["Pythonistas"])

        # Make sure that if no rows are found, an empty list is returned.
        empty_response = (
            Band.select(Band.name)
            .where(Band.name == "ABC123")
            .output(as_list=True)
            .run_sync()
        )
        self.assertEqual(empty_response, [])


class TestOutputJSON(DBTestCase):
    def test_output_as_json(self):
        self.insert_row()

        response = Band.select(Band.name).output(as_json=True).run_sync()

        self.assertEqual(json.loads(response), [{"name": "Pythonistas"}])


class TestOutputLoadJSON(TestCase):
    def setUp(self):
        RecordingStudio.create_table().run_sync()

    def tearDown(self):
        RecordingStudio.alter().drop_table().run_sync()

    def test_select(self):
        json = {"a": 123}

        RecordingStudio(facilities=json, facilities_b=json).save().run_sync()

        results = (
            RecordingStudio.select(
                RecordingStudio.facilities, RecordingStudio.facilities_b
            )
            .output(load_json=True)
            .run_sync()
        )

        self.assertEqual(
            results,
            [
                {
                    "facilities": json,
                    "facilities_b": json,
                }
            ],
        )

    def test_objects(self):
        json = {"a": 123}

        RecordingStudio(facilities=json, facilities_b=json).save().run_sync()

        results = RecordingStudio.objects().output(load_json=True).run_sync()

        self.assertEqual(results[0].facilities, json)
        self.assertEqual(results[0].facilities_b, json)


class TestLoadJSONWithJoin(TestCase):
    """
    Make sure ``output(load_json=True)`` works correctly when the JSON column
    is on a joined table.

    https://github.com/piccolo-orm/piccolo/issues/1001

    """

    tables = [RecordingStudio, Instrument]
    json = {"a": 123}

    def setUp(self):
        create_db_tables_sync(*self.tables)

        recording_studio = RecordingStudio(
            {
                RecordingStudio.facilities: json,
                RecordingStudio.facilities_b: json,
            }
        )
        recording_studio.save().run_sync()

        instrument = Instrument(
            {
                Instrument.recording_studio: recording_studio,
                Instrument.name: "Piccolo",
            }
        )
        instrument.save().run_sync()

    def tearDown(self):
        drop_db_tables_sync(*self.tables)

    def test_select(self):
        results = (
            Instrument.select(
                Instrument.name,
                Instrument.recording_studio._.facilities,
            )
            .output(load_json=True)
            .run_sync()
        )

        self.assertEqual(
            results,
            [
                {
                    "name": "Piccolo",
                    "recording_studio.facilities": json,
                }
            ],
        )

    def test_select_with_alias(self):
        results = (
            Instrument.select(
                Instrument.name,
                Instrument.recording_studio._.facilities.as_alias(
                    "facilities"
                ),
            )
            .output(load_json=True)
            .run_sync()
        )

        self.assertEqual(
            results,
            [
                {
                    "name": "Piccolo",
                    "recording_studio.facilities": json,
                }
            ],
        )


class TestOutputNested(DBTestCase):
    def test_output_nested(self):
        self.insert_row()

        response = (
            Band.select(Band.name, Band.manager.name)
            .output(nested=True)
            .run_sync()
        )
        self.assertEqual(
            response, [{"name": "Pythonistas", "manager": {"name": "Guido"}}]
        )

    def test_output_nested_with_first(self):
        self.insert_row()

        response = (
            Band.select(Band.name, Band.manager.name)
            .first()
            .output(nested=True)
            .run_sync()
        )
        assert response is not None
        self.assertDictEqual(
            response,  # type: ignore
            {"name": "Pythonistas", "manager": {"name": "Guido"}},
        )
