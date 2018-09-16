from tests.example_project.tables import Pokemon
from tests.base import DBTestCase


class TestDelete(DBTestCase):

    def setUp(self):
        Pokemon.create().run_sync()

    def tearDown(self):
        Pokemon.drop().run_sync()

    def test_delete(self):

        squirtle = Pokemon(
            name='squirtle',
            trainer='Misty',
            power=300
        )

        squirtle.save().run_sync()
        squirtle.delete().run_sync()

        # how can I implement 'flat=True'
        # Pokemon.select('name').output(as_list=True).run_sync()
        #
        Pokemon.select('name').run_sync()
