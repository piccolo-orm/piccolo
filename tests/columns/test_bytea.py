from unittest import TestCase

from piccolo.columns.column_types import Bytea
from piccolo.table import Table


class MyTable(Table):
    token = Bytea()


class MyTableDefault(Table):
    """
    Test the different default types.
    """

    token = Bytea()
    token_bytes = Bytea(default=b"my-token")
    token_bytearray = Bytea(default=bytearray(b"my-token"))
    token_none = Bytea(default=None, null=True)


class TestBytea(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_bytea(self):
        """
        Test storing a valid bytes value.
        """
        row = MyTable(token=b"my-token")
        row.save().run_sync()
        self.assertEqual(row.token, b"my-token")

        self.assertEqual(
            MyTable.select(MyTable.token).first().run_sync(),
            {"token": b"my-token"},
        )


class TestByteaDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_json_default(self):
        row = MyTableDefault()
        row.save().run_sync()

        self.assertEqual(row.token, b"")
        self.assertEqual(row.token_bytes, b"my-token")
        self.assertEqual(row.token_bytearray, b"my-token")
        self.assertEqual(row.token_none, None)

    def test_invalid_default(self):
        with self.assertRaises(ValueError):
            for value in ("a", 1, ("x", "y", "z")):
                Bytea(default=value)
