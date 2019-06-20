from piccolo.columns import Integer

from .base import DBTestCase
from .example_project.tables import Band


class TestRename(DBTestCase):

    def test_rename(self):
        self.insert_row()

        rename_query = Band.alter.rename(
            Band.popularity,
            'rating'
        )

        rename_query.run_sync()

        # The problem now is select * has changed
        # Need to use a raw select query instead ...
        select_query = Band.select
        response = select_query.run_sync()

        column_names = response[0].keys()
        self.assertTrue(
            ('rating' in column_names) and ('popularity' not in column_names)
        )


class TestDrop(DBTestCase):

    def test_drop(self):
        self.insert_row()

        Band.alter.drop(
            Band.popularity,
        ).run_sync()

        response = Band.select.run_sync()

        column_names = response[0].keys()
        self.assertTrue(
            'popularity' not in column_names
        )


class TestAdd(DBTestCase):

    def test_add(self):
        """
        This needs a lot more work. Need to set values for existing rows.

        Just write the test for now ...
        """
        self.insert_row()

        add_query = Band.alter.add(
            'weight',
            Integer(),
        )
        add_query.run_sync()

        select_query = Band.select
        response = select_query.run_sync()

        column_names = response[0].keys()
        self.assertTrue('weight' in column_names)

        self.assertEqual(response[0]['weight'], None)


class TestMultiple(DBTestCase):
    pass
