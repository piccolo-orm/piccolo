from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Array, Integer
from tests.base import postgres_only


class MyTable(Table):
    value = Array(base_column=Integer())


class TestArrayPostgres(TestCase):
    """
    Make sure an Array column can be created.
    """

    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_storage(self):
        """
        Make sure data can be stored and retrieved.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()

        row = MyTable.objects().first().run_sync()
        self.assertEqual(row.value, [1, 2, 3])

    @postgres_only
    def test_index(self):
        """
        Indexes should allow individual array elements to be queried.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value[0]).first().run_sync(), {"value": 1}
        )
