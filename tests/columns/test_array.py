from unittest import TestCase

from piccolo.columns.column_types import Array, Integer
from piccolo.table import Table
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

    @postgres_only
    def test_all(self):
        """
        Make sure rows can be retrieved where all items in an array match a
        given value.
        """
        MyTable(value=[1, 1, 1]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.all(1))
            .first()
            .run_sync(),
            {"value": [1, 1, 1]},
        )

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.all(0))
            .first()
            .run_sync(),
            None,
        )

    def test_any(self):
        """
        Make sure rows can be retrieved where any items in an array match a
        given value.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.any(1))
            .first()
            .run_sync(),
            {"value": [1, 2, 3]},
        )

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.any(0))
            .first()
            .run_sync(),
            None,
        )
