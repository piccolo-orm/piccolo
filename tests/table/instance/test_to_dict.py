from tests.base import DBTestCase
from tests.example_app.tables import Manager


class TestToDict(DBTestCase):
    def test_to_dict(self):
        """
        Make sure that `to_dict` works correctly.
        """
        self.insert_row()

        instance = Manager.objects().first().run_sync()
        dictionary = instance.to_dict()
        self.assertEqual(dictionary, {"id": 1, "name": "Guido"})
