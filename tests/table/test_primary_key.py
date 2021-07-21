import uuid
import pytest
from unittest import TestCase

from piccolo.columns.column_types import UUID, Integer, Varchar
from piccolo.table import Table


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

    @pytest.mark.skip
    def test_return_type(self):
        row = MyTablePrimaryKeyUUID()
        row.save().run_sync()

        self.assertIsInstance(row.id, uuid.UUID)
