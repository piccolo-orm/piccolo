from unittest import TestCase

from tests.example_project.tables import Pokemon, Stadium, Match


class TestGetRelated(TestCase):

    def setUp(self):
        Pokemon.create().run_sync()
        Stadium.create().run_sync()
        Match.create().run_sync()

    def tearDown(self):
        Match.drop().run_sync()
        Pokemon.drop().run_sync()
        Stadium.drop().run_sync()

    def test_get_related(self):
        """
        Make sure you can get a related object from another object instance.
        """
        pikachu = Pokemon(
            name='pikachu'
        )
        pikachu.save().run_sync()

        squirtle = Pokemon(
            name='squirtle'
        )
        squirtle.save().run_sync()

        stadium = Stadium(
            name="red stadium"
        )
        stadium.save().run_sync()

        match = Match(
            pokemon_1=pikachu.id,
            pokemon_2=squirtle.id,
            stadium=stadium.id
        )
        match.save().run_sync()

        _match = Match.objects().where(
            Match.id == match.id
        ).first().run_sync()

        _stadium = _match.get_related('stadium').run_snyc()

        self.assertTrue(
            _stadium.name == 'red stadium'
        )
