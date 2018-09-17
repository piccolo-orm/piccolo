from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestObjects(DBTestCase):

    def test_get_all(self):
        self.insert_row()

        response = Pokemon.objects().run_sync()

        self.assertTrue(len(response) == 1)
        self.assertTrue(isinstance(response[0], Pokemon))
        self.assertTrue(response[0].name == 'pikachu')
