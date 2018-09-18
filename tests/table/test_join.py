from unittest import TestCase

from ..example_project.tables import Pokemon, Stadium, Match


# class TestCreateJoin():

#     def test_create_join(self):

#         Pokemon.create().run_sync()
#         Stadium.create().run_sync()
#         Match.create().run_sync()

#         Match.drop().run_sync()
#         Pokemon.drop().run_sync()
#         Stadium.drop().run_sync()


class TestJoin(TestCase):
    """
    Test instantiating Table instances
    """

    def setUp(self):
        Pokemon.create().run_sync()
        Stadium.create().run_sync()
        Match.create().run_sync()

    def tearDown(self):
        Match.drop().run_sync()
        Pokemon.drop().run_sync()
        Stadium.drop().run_sync()

    def test_join(self):
        pikachu = Pokemon(name="pikachu", trainer="ash")
        pikachu.save().run_sync()

        bulbasaur = Pokemon(name="bulbasaur")
        bulbasaur.save().run_sync()

        stadium = Stadium(name="fairy garden")
        stadium.save().run_sync()

        # TODO - make sure you can also do:
        # pokemon_1=pikachu
        save_query = Match(
            pokemon_1=pikachu.id,
            pokemon_2=bulbasaur.id,
            stadium=stadium.id
        ).save()
        save_query.run_sync()

        select_query = Match.select(
            'pokemon_1.name',
            'pokemon_2.name',
            'stadium.name',
            'pokemon_1.trainer'
        )
        response = select_query.run_sync()
        print(response)


    # def _test_ref(self):
    #     """
    #     Match.select().count().where(
    #         Match.ref('pokemon1.name') == 'pikachu'
    #     )
    #     """
    #     pass
