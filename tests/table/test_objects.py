from ..base import DBTestCase
from ..example_project.tables import Band


class TestObjects(DBTestCase):

    def test_get_all(self):
        self.insert_row()

        response = Band.objects.run_sync()

        self.assertTrue(len(response) == 1)

        instance = response[0]

        self.assertTrue(isinstance(instance, Band))
        self.assertTrue(instance.name == 'Pythonistas')

        # Now try changing the value and saving it.
        instance.name = 'Rustaceans'
        save_query = instance.save
        save_query.run_sync()

        self.assertTrue(
            Band.select.columns(
                Band.name
            ).output(
                as_list=True
            ).run_sync()[0] == 'Rustaceans'
        )
