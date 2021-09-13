from unittest import TestCase

from piccolo.columns.column_types import Varchar
from tests.example_apps.music.tables import Band


class TestRef(TestCase):
    def test_ref(self):
        column = Band.ref("manager.name")
        self.assertTrue(isinstance(column, Varchar))
