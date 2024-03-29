from tests.base import DBTestCase, engine_is
from tests.example_apps.music.tables import Band, Manager


class TestToDict(DBTestCase):
    def test_to_dict(self):
        """
        Make sure that `to_dict` works correctly.
        """
        self.insert_row()

        instance = Manager.objects().first().run_sync()
        assert instance is not None
        dictionary = instance.to_dict()
        if engine_is("cockroach"):
            self.assertDictEqual(
                dictionary, {"id": dictionary["id"], "name": "Guido"}
            )
        else:
            self.assertDictEqual(dictionary, {"id": 1, "name": "Guido"})

    def test_nested(self):
        """
        Make sure that `to_dict` works correctly, when the object contains
        nested objects.
        """
        self.insert_row()

        instance = Band.objects(Band.manager).first().run_sync()
        assert instance is not None
        dictionary = instance.to_dict()
        if engine_is("cockroach"):
            self.assertDictEqual(
                dictionary,
                {
                    "id": dictionary["id"],
                    "name": "Pythonistas",
                    "manager": {
                        "id": instance["manager"]["id"],
                        "name": "Guido",
                    },
                    "popularity": 1000,
                },
            )
        else:
            self.assertDictEqual(
                dictionary,
                {
                    "id": 1,
                    "name": "Pythonistas",
                    "manager": {"id": 1, "name": "Guido"},
                    "popularity": 1000,
                },
            )

    def test_filter_rows(self):
        """
        Make sure that `to_dict` works correctly with a subset of columns.
        """
        self.insert_row()

        instance = Manager.objects().first().run_sync()
        assert instance is not None
        dictionary = instance.to_dict(Manager.name)
        self.assertDictEqual(dictionary, {"name": "Guido"})

    def test_nested_filter(self):
        """
        Make sure that `to_dict` works correctly with nested objects and
        filtering.
        """
        self.insert_row()

        instance = Band.objects(Band.manager).first().run_sync()
        assert instance is not None
        dictionary = instance.to_dict(Band.name, Band.manager.id)
        if engine_is("cockroach"):
            self.assertDictEqual(
                dictionary,
                {
                    "name": "Pythonistas",
                    "manager": {"id": dictionary["manager"]["id"]},
                },
            )
        else:
            self.assertDictEqual(
                dictionary,
                {
                    "name": "Pythonistas",
                    "manager": {"id": 1},
                },
            )

    def test_aliases(self):
        """
        Make sure that `to_dict` works correctly with aliases.
        """
        self.insert_row()

        instance = Manager.objects().first().run_sync()
        assert instance is not None
        dictionary = instance.to_dict(
            Manager.id, Manager.name.as_alias("title")
        )
        if engine_is("cockroach"):
            self.assertDictEqual(
                dictionary, {"id": dictionary["id"], "title": "Guido"}
            )
        else:
            self.assertDictEqual(dictionary, {"id": 1, "title": "Guido"})
