from tests.example_project.tables import Pokemon
from tests.base import DBTestCase


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

        names = [i['name'] for i in Pokemon.select('name').run_sync()]
        self.assertTrue('squirtle' in names)

        squirtle.name = 'blastoise'
        query = squirtle.save()
        print(query)
        self.assertTrue('UPDATE' in query.__str__())

        query.run_sync()
        names = [i['name'] for i in Pokemon.select('name').run_sync()]
        self.assertTrue('blastoise' in names)
        self.assertTrue('squirtle' not in names)

        # Make sure it has an id too ...
        # and the next query is an UPDATE ...
        # .run(objects=True)
        # .run(as_json=True)
        # Generic('some_table').select('name')
        # -> won't work because where requires things like
        # Pokemon.select().where(Pokemon.id == 1)
        # So doesn't work as a generic query build without first defining
        # the tables.... this is totally fine though.
