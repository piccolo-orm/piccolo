from unittest import TestCase

from ..example_project.tables import Band, Stadium, Concert


class TestCreateJoin():

    def test_create_join(self):

        Band.create().run_sync()
        Stadium.create().run_sync()
        Concert.create().run_sync()

        Concert.drop().run_sync()
        Band.drop().run_sync()
        Stadium.drop().run_sync()


class TestJoin(TestCase):
    """
    Test instantiating Table instances
    """

    def setUp(self):
        Band.create().run_sync()
        Stadium.create().run_sync()
        Concert.create().run_sync()

    def tearDown(self):
        Concert.drop().run_sync()
        Band.drop().run_sync()
        Stadium.drop().run_sync()

    def test_join(self):
        pikachu = Band(name="pikachu", manager="ash")
        pikachu.save().run_sync()

        bulbasaur = Band(name="bulbasaur")
        bulbasaur.save().run_sync()

        stadium = Stadium(name="fairy garden")
        stadium.save().run_sync()

        # TODO - make sure you can also do:
        # band_1=pikachu
        save_query = Concert(
            band_1=pikachu.id,
            band_2=bulbasaur.id,
            stadium=stadium.id
        ).save()
        save_query.run_sync()

        select_query = Concert.select(
            'band_1.name',
            'band_2.name',
            'stadium.name',
            'band_1.manager'
        )
        response = select_query.run_sync()
        print(response)

    # def _test_ref(self):
    #     """
    #     Concert.select().count().where(
    #         Concert.ref('band1.name') == 'pikachu'
    #     )
    #     """
    #     pass
