from piccolo.apps.fixture.commands.dump import dump_to_json_string
from piccolo.apps.fixture.commands.load import load_json_string
from piccolo.utils.sync import run_sync
from tests.base import DBTestCase
from tests.example_app.tables import Band, Manager


class TestDumpLoad(DBTestCase):
    """
    Test the dump and load commands - makes sense to test them together.
    """

    def test_dump_load(self):
        self.insert_rows()
        json_string = run_sync(
            dump_to_json_string(apps="example_app", tables="Band,Manager")
        )

        # We need to clear the data out now, otherwise when loading the data
        # back in, there will be a constraint errors over clashing primary
        # keys.
        Band.delete(force=True).run_sync()
        Manager.delete(force=True).run_sync()

        run_sync(load_json_string(json_string))

        self.assertEqual(
            Band.select().run_sync(),
            [
                {
                    "id": 1,
                    "name": "Pythonistas",
                    "manager": 1,
                    "popularity": 1000,
                },
                {
                    "id": 2,
                    "name": "Rustaceans",
                    "manager": 2,
                    "popularity": 2000,
                },
                {"id": 3, "name": "CSharps", "manager": 3, "popularity": 10},
            ],
        )

        self.assertEqual(
            Manager.select().run_sync(),
            [
                {"id": 1, "name": "Guido"},
                {"id": 2, "name": "Graydon"},
                {"id": 3, "name": "Mads"},
            ],
        )
