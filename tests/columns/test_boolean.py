from unittest import TestCase

from piccolo.columns.column_types import Boolean
from piccolo.table import Table


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
                .where(
                    MyTable._meta.primary_key
                    == getattr(row, MyTable._meta.primary_key._meta.name)
                )
                .first()
                .run_sync()["boolean"],
                expected,
            )

    def test_eq_and_ne(self):
        """
        Make sure the `eq` and `ne` methods works correctly.
        """
        MyTable.insert(
            MyTable(boolean=True),
            MyTable(boolean=False),
            MyTable(boolean=True),
        ).run_sync()

        self.assertEqual(
            MyTable.count().where(MyTable.boolean.eq(True)).run_sync(), 2
        )

        self.assertEqual(
            MyTable.count().where(MyTable.boolean.ne(True)).run_sync(), 1
        )
