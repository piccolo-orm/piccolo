from ..base import DBTestCase
from ..example_project.tables import Band, Manager


class TestInsert(DBTestCase):

    def test_insert(self):
        self.insert_rows()

        Band.insert(
            Band(name='bulbasaur')
        ).run_sync()

        response = Band.select('name').run_sync()
        names = [i['name'] for i in response]

        self.assertTrue(
            'bulbasaur' in names
        )

    def test_add(self):
        self.insert_rows()

        Band.insert().add(
            Band(name='bulbasaur')
        ).run_sync()

        response = Band.select('name').run_sync()
        names = [i['name'] for i in response]

        self.assertTrue(
            'bulbasaur' in names
        )

    def test_incompatible_type(self):
        """
        You shouldn't be able to add instances of a different table.
        """
        with self.assertRaises(TypeError):
            Band.insert().add(
                Manager(name="Ash")
            ).run_sync()
