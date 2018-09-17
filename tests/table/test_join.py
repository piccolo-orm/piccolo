from unittest import TestCase

from ..example_project.tables import Pokemon, Stadium, Match


class TestJoin(TestCase):
    """
    Test instantiating Table instances
    """

    def setUp(self):
        Pokemon.create().run_sync()
        Stadium.create().run_sync()
        Match.create().run_sync()

    def tearDown(self):
        Match.delete().run_sync()
        Pokemon.delete().run_sync()
        Stadium.delete().run_sync()

    def test_join(self):
        """
        Need a good example ...
        """
        pikachu = Pokemon(name="pikachu")
        pikachu.save().run_sync()

        bulbasaur = Pokemon(name="bulbasaur")
        bulbasaur.save().run_sync()

        stadium = Stadium(name="fairy garden")

        Match(
            pokemon1=pikachu,
            pokemon2=bulbasaur,
            stadium=stadium
        ).save().run_sync()

        response = Match.select(
            'pokemon1.name',
            'pokemon2.name',
            'stadium.name'
        ).run_sync()
