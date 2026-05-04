from tests.base import DBTestCase
from tests.example_apps.music.tables import Band


class TestExists(DBTestCase):
    def test_exists(self):
        self.insert_rows()

        response = Band.exists().where(Band.name == "Pythonistas").run_sync()

        self.assertTrue(response)
