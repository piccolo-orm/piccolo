import json

from ..base import DBTestCase
from ..example_app.tables import Band


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
