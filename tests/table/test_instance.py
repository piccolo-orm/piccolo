from ..base import DBTestCase
from ..example_project.tables import Band


class TestInstance(DBTestCase):
    """
    Test instantiating Table instances
    """

    def test_insert(self):
        Pythonistas = Band(name="Pythonistas")
        self.assertEqual(Pythonistas.__str__(), "('Pythonistas',null,null,DEFAULT)")

    def test_non_existant_column(self):
        with self.assertRaises(ValueError):
            Band(name="Pythonistas", foo="bar")
