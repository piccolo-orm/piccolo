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

    def test_filter_rows(self):
        """
        Make sure that `to_dict` works correctly with a subset of columns.
        """
        self.insert_row()

        instance = Manager.objects().first().run_sync()
        dictionary = instance.to_dict(Manager.name)
        self.assertEqual(dictionary, {"name": "Guido"})

    def test_to_dict_aliases(self):
        """
        Make sure that `to_dict` works correctly with aliases.
        """
        self.insert_row()

        instance = Manager.objects().first().run_sync()
        dictionary = instance.to_dict(
            Manager.id, Manager.name.as_alias("title")
        )
        self.assertEqual(dictionary, {"id": 1, "title": "Guido"})
