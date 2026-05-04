from unittest import TestCase

from piccolo.columns import Integer, Varchar
from piccolo.table import Table


class Band(Table):
    name = Varchar()
    popularity = Integer()


class TestCount(TestCase):
    def setUp(self) -> None:
        Band.create_table().run_sync()

    def tearDown(self) -> None:
        Band.alter().drop_table().run_sync()

    def test_count(self):
        Band.insert(
            Band(name="Pythonistas", popularity=10),
            Band(name="Rustaceans", popularity=10),
            Band(name="C-Sharps", popularity=5),
        ).run_sync()

        response = Band.count().run_sync()

        self.assertEqual(response, 3)

    def test_count_where(self):
        Band.insert(
            Band(name="Pythonistas", popularity=10),
            Band(name="Rustaceans", popularity=10),
            Band(name="C-Sharps", popularity=5),
        ).run_sync()

        response = Band.count().where(Band.popularity == 10).run_sync()

        self.assertEqual(response, 2)

    def test_count_distinct(self):
        Band.insert(
            Band(name="Pythonistas", popularity=10),
            Band(name="Rustaceans", popularity=10),
            Band(name="C-Sharps", popularity=5),
            Band(name="Fortranists", popularity=2),
        ).run_sync()

        response = Band.count(distinct=[Band.popularity]).run_sync()

        self.assertEqual(response, 3)

        # Test the method also works
        response = Band.count().distinct([Band.popularity]).run_sync()
        self.assertEqual(response, 3)

    def test_count_distinct_multiple(self):
        Band.insert(
            Band(name="Pythonistas", popularity=10),
            Band(name="Pythonistas", popularity=10),
            Band(name="Rustaceans", popularity=10),
            Band(name="C-Sharps", popularity=5),
            Band(name="Fortranists", popularity=2),
        ).run_sync()

        response = Band.count(distinct=[Band.name, Band.popularity]).run_sync()

        self.assertEqual(response, 4)

    def test_value_error(self):
        """
        Make sure specifying `column` and `distinct` raises an error.
        """
        with self.assertRaises(ValueError):
            Band.count(
                column=Band.name, distinct=[Band.name, Band.popularity]
            ).run_sync()
