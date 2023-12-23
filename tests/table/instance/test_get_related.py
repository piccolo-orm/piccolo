import typing as t
from unittest import TestCase

from tests.example_apps.music.tables import Band, Manager

TABLES = [Manager, Band]


class TestGetRelated(TestCase):
    def setUp(self):
        for table in TABLES:
            table.create_table().run_sync()

    def tearDown(self):
        for table in reversed(TABLES):
            table.alter().drop_table().run_sync()

    def test_get_related(self) -> None:
        """
        Make sure you can get a related object from another object instance.
        """
        manager = Manager(name="Guido")
        manager.save().run_sync()

        band = Band(name="Pythonistas", manager=manager.id, popularity=100)
        band.save().run_sync()

        _manager = band.get_related(Band.manager).run_sync()
        assert _manager is not None
        self.assertTrue(_manager.name == "Guido")

        # Test non-ForeignKey
        with self.assertRaises(ValueError):
            band.get_related(Band.name)  # type: ignore

        # Make sure it also works using a string
        _manager_2 = t.cast(Manager, band.get_related("manager").run_sync())
        self.assertTrue(_manager_2.name == "Guido")

        # Test an invalid string
        with self.assertRaises(ValueError):
            band.get_related("abc123")
