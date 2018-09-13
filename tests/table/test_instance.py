from ..base import DBTestCase
from ..example_project.tables import Pokemon


class TestInstance(DBTestCase):
    """
    Test instantiating Table instances
    """

    def test_insert(self):
        pikachu = Pokemon(name="pikachu")
        self.assertEqual(pikachu.__str__(), "(DEFAULT,'pikachu',null,null)")

    def test_non_existant_column(self):
        with self.assertRaises(ValueError):
            Pokemon(name="pikachu", foo="bar")
