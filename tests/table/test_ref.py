from unittest import TestCase
from tests.example_app.tables import Band

from piccolo.columns.column_types import Varchar


class TestRef(TestCase):
    def test_ref(self):
        column = Band.ref("manager.name")
        self.assertTrue(isinstance(column, Varchar))
