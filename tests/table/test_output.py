import json

from ..base import DBTestCase
from ..example_project.tables import Band


class TestOutput(DBTestCase):
    def test_output_as_list(self):
        self.insert_row()

        response = Band.select(Band.name).output(as_list=True).run_sync()

        self.assertTrue(response == ["Pythonistas"])

    def test_output_as_json(self):
        self.insert_row()

        response = Band.select(Band.name).output(as_json=True).run_sync()

        self.assertTrue(json.loads(response) == [{"name": "Pythonistas"}])
