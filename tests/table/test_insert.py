from ..base import DBTestCase
from ..example_project.tables import Pokemon, Trainer


class TestInsert(DBTestCase):

    def test_insert(self):
        self.insert_rows()

        query = Pokemon.insert().add(
            Pokemon(name='bulbasaur')
        )
        print(query)

        query.run_sync()

        response = Pokemon.select('name').run_sync()

        print(f'response = {response}')
        names = [i['name'] for i in response]

        self.assertTrue(
            'bulbasaur' in names
        )

    def test_incompatible_type(self):
        """
        You shouldn'e be able to add instances of a different table.
        """
        with self.assertRaises(TypeError):
            Pokemon.insert().add(
                Trainer(name="Ash")
            ).run_sync()
