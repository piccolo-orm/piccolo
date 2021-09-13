from tests.example_apps.music.tables import Band

from ..base import DBTestCase


class TestCount(DBTestCase):
    def test_exists(self):
        self.insert_rows()

        response = Band.count().where(Band.name == "Pythonistas").run_sync()

        self.assertTrue(response == 1)
