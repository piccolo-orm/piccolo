from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Boolean


class MyTable(Table):
    boolean = Boolean(boolean=False, null=True)


class TestBoolean(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_return_type(self):
        for value in (True, False, None, ...):
            kwargs = {} if value is ... else {"boolean": value}
            expected = MyTable.boolean.default if value is ... else value

            row = MyTable(**kwargs)
            row.save().run_sync()
            self.assertEqual(row.boolean, expected)

            self.assertEqual(
                MyTable.select(MyTable.boolean)
                .where(MyTable.id == row.id)
                .first()
                .run_sync()["boolean"],
                expected,
            )
