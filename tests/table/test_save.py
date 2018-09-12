from ..example_project.tables import Pokemon
from ..base import DBTestCase


class TestSave(DBTestCase):

    def setUp(self):
        Pokemon.create().run_sync()

    def tearDown(self):
        Pokemon.drop().run_sync()

    def test_save_new(self):
        """
        Make sure that saving a new
        """
        self.insert_rows()

        squirtle = Pokemon(
            name='squirtle',
            trainer='Misty',
            power=300
        )

        query = squirtle.save()
        print(query)
        self.assertTrue('INSERT' in query.__str__())

        query.run_sync()

        self.assertTrue(
            'squirtle' in [
                i['name'] for i in Pokemon.select('name').run_sync()
            ]
        )

        # Make sure it has an id too ...
        # and the next query is an UPDATE ...
