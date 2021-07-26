import uuid
from unittest import TestCase

from piccolo.columns.column_types import UUID, Serial, Varchar
from piccolo.table import Table


class MyTableDefaultPrimaryKey(Table):
    name = Varchar()


class MyTablePrimaryKeySerial(Table):
    pk = Serial(null=False, primary=True, key=True)
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

        self.assertIsInstance(row._meta.primary_key, int)


class TestPrimaryKeyInteger(TestCase):
    def setUp(self):
        MyTablePrimaryKeySerial.create_table().run_sync()

    def tearDown(self):
        MyTablePrimaryKeySerial.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTablePrimaryKeySerial()
        result = row.save().run_sync()[0]

        self.assertIsInstance(result["pk"], int)


class TestPrimaryKeyUUID(TestCase):
    def setUp(self):
        MyTablePrimaryKeyUUID.create_table().run_sync()

    def tearDown(self):
        MyTablePrimaryKeyUUID.alter().drop_table().run_sync()

    def test_return_type(self):
        row = MyTablePrimaryKeyUUID()
        row.save().run_sync()

        self.assertIsInstance(row.id, uuid.UUID)
