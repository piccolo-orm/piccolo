import json
from unittest import TestCase

from tests.base import DBTestCase
from tests.example_app.tables import Band, RecordingStudio


class TestOutputList(DBTestCase):
    def test_output_as_list(self):
        self.insert_row()

        response = Band.select(Band.name).output(as_list=True).run_sync()
        self.assertTrue(response == ["Pythonistas"])

        # Make sure that if no rows are found, an empty list is returned.
        empty_response = (
            Band.select(Band.name)
            .where(Band.name == "ABC123")
            .output(as_list=True)
            .run_sync()
        )
        self.assertTrue(empty_response == [])


class TestOutputJSON(DBTestCase):
    def test_output_as_json(self):
        self.insert_row()

        response = Band.select(Band.name).output(as_json=True).run_sync()

        self.assertTrue(json.loads(response) == [{"name": "Pythonistas"}])


class TestOutputLoadJSON(TestCase):
    def setUp(self):
        RecordingStudio.create_table().run_sync()

    def tearDown(self):
        RecordingStudio.alter().drop_table().run_sync()

    def test_select(self):
        json = {"a": 123}

        RecordingStudio(facilities=json, facilities_b=json).save().run_sync()

        results = RecordingStudio.select().output(load_json=True).run_sync()

        self.assertEqual(
            results,
            [{"id": 1, "facilities": {"a": 123}, "facilities_b": {"a": 123}}],
        )

    def test_objects(self):
        json = {"a": 123}

        RecordingStudio(facilities=json, facilities_b=json).save().run_sync()

        results = RecordingStudio.objects().output(load_json=True).run_sync()

        self.assertEqual(results[0].facilities, json)
        self.assertEqual(results[0].facilities_b, json)
