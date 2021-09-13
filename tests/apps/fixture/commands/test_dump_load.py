from unittest import TestCase

from piccolo.apps.fixture.commands.dump import dump_to_json_string
from piccolo.apps.fixture.commands.load import load_json_string
from piccolo.utils.sync import run_sync
from tests.example_apps.mega.tables import MegaTable, SmallTable


class TestDumpLoad(TestCase):
    """
    Test the dump and load commands - makes sense to test them together.
    """

    def setUp(self):
        for table_class in (SmallTable, MegaTable):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (MegaTable, SmallTable):
            table_class.alter().drop_table().run_sync()

    def _test_dump_load(self):
        json_string = run_sync(
            dump_to_json_string(apps="example_app", tables="Band,Manager")
        )

        # We need to clear the data out now, otherwise when loading the data
        # back in, there will be a constraint errors over clashing primary
        # keys.
        SmallTable.delete(force=True).run_sync()
        MegaTable.delete(force=True).run_sync()

        run_sync(load_json_string(json_string))

        self.assertEqual(
            SmallTable.select().run_sync(),
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
            MegaTable.select().run_sync(),
            [
                {"id": 1, "name": "Guido"},
                {"id": 2, "name": "Graydon"},
                {"id": 3, "name": "Mads"},
            ],
        )
