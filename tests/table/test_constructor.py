from unittest import TestCase

from tests.example_apps.music.tables import Band


class TestConstructor(TestCase):
    def test_data_parameter(self):
        """
        Make sure the _data parameter works.
        """
        band = Band({Band.name: "Pythonistas"})
        self.assertEqual(band.name, "Pythonistas")

    def test_kwargs(self):
        """
        Make sure kwargs works.
        """
        band = Band(name="Pythonistas")
        self.assertEqual(band.name, "Pythonistas")

    def test_mix(self):
        """
        Make sure the _data paramter and kwargs works together (it's unlikely
        people will do this, but just in case).
        """
        band = Band({Band.name: "Pythonistas"}, popularity=1000)
        self.assertEqual(band.name, "Pythonistas")
        self.assertEqual(band.popularity, 1000)
