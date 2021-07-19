from unittest import TestCase
import uuid

from piccolo.table import Table
from piccolo.columns.column_types import Integer, UUID, Varchar


class MyTableDefaultPrimaryKey(Table):
    name = Varchar()


class MyTablePrimaryKeyInteger(Table):
    id = Integer(null=False, primary=True, key=True)
    name = Varchar()


class MyTablePrimaryKeyUUID(Table):
    id = UUID(null=False, primary=True, key=True)
    name = Varchar()


class TestPrimaryKeyDefault(TestCase):
    def setUp(self):
        MyTableDefaultPrimaryKey.create_table().run_sync()

    def tearDown(self):
        MyTableDefaultPrimaryKey.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTableDefaultPrimaryKey()
        row.save().run_sync()

        self.assertIsInstance(row.id, int)


class TestPrimaryKeyInteger(TestCase):
    def setUp(self):
        MyTablePrimaryKeyInteger.create_table().run_sync()

    def tearDown(self):
        MyTablePrimaryKeyInteger.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTablePrimaryKeyInteger()
        row.save().run_sync()

        self.assertIsInstance(row.id, int)


class TestPrimaryKeyUUID(TestCase):
    def setUp(self):
        MyTablePrimaryKeyUUID.create_table().run_sync()

    def tearDown(self):
        MyTablePrimaryKeyUUID.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTablePrimaryKeyUUID()
        row.save().run_sync()

        self.assertIsInstance(row.id, uuid.UUID)
