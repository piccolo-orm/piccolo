from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Varchar


class MyTable(Table):
    name = Varchar(length=10)


class TestVarchar(TestCase):
    def test_length(self):
        MyTable.create().run_sync()

