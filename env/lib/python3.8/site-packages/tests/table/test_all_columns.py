from unittest import TestCase

from tests.example_apps.music.tables import Band


class TestAllColumns(TestCase):
    def test_all_columns(self):
        self.assertEqual(
            Band.all_columns(),
            [Band.id, Band.name, Band.manager, Band.popularity],
        )
        self.assertEqual(Band.all_columns(), Band._meta.columns)

    def test_all_columns_excluding(self):
        self.assertEqual(
            Band.all_columns(exclude=[Band.id]),
            [Band.name, Band.manager, Band.popularity],
        )

        self.assertEqual(
            Band.all_columns(exclude=["id"]),
            [Band.name, Band.manager, Band.popularity],
        )
