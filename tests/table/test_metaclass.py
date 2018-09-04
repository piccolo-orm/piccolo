from unittest import TestCase

from ..example_project.tables import Pokemon


class TestMetaClass(TestCase):

    def test_tablename(self):
        self.assertEqual(Pokemon.Meta.tablename, 'pokemon')
