from unittest import TestCase

from ..example_project.tables import Band


class TestMetaClass(TestCase):

    def test_tablename(self):
        self.assertEqual(Band._meta.tablename, 'band')
