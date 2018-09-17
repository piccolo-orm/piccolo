from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestObjects(DBTestCase):

    def test_get_all(self):
        self.insert_row()

        response = Pokemon.objects().run_sync()

        self.assertTrue(len(response) == 1)

        instance = response[0]

        self.assertTrue(isinstance(instance, Pokemon))
        self.assertTrue(instance.name == 'pikachu')

        # No try changing the value and saving it.
        instance.name = 'raichu'
        instance.save().run_sync()

        self.assertTrue(
            Pokemon.select(
                'name'
            ).output(
                as_list=True
            ).run_sync()[0] == 'raichu'
        )
