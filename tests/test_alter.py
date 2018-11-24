from piccolo.columns import Integer

from .base import DBTestCase
from .example_project.tables import Band


class TestRename(DBTestCase):

    def test_rename(self):
        self.insert_row()

        Band.alter().rename(
            Band.power,
            'rating'
        ).run_sync()

        response = Band.select().run_sync()

        column_names = response[0].keys()
        self.assertTrue(
            ('rating' in column_names) and ('power' not in column_names)
        )


class TestDrop(DBTestCase):

    def test_drop(self):
        self.insert_row()

        Band.alter().drop(
            Band.power,
        ).run_sync()

        response = Band.select().run_sync()

        column_names = response[0].keys()
        self.assertTrue(
            'power' not in column_names
        )


class TestAdd(DBTestCase):

    def test_add(self):
        """
        This needs a lot more work. Need to set values for existing rows.

        Just write the test for now ...
        """
        self.insert_row()

        Band.alter().add(
            'weight',
            Integer(),
        ).run_sync()

        response = Band.select().run_sync()

        column_names = response[0].keys()
        self.assertTrue('weight' in column_names)

        self.assertEqual(response[0]['weight'], None)


class TestMultiple(DBTestCase):
    pass
