import datetime
from unittest import TestCase

from piccolo.columns.column_types import Date
from piccolo.columns.defaults.date import DateNow
from piccolo.table import Table


class MyTable(Table):
    created_on = Date()


class MyTableDefault(Table):
    created_on = Date(default=DateNow())


class TestDate(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_timestamp(self):
        created_on = datetime.datetime.now().date()
        row = MyTable(created_on=created_on)
        row.save().run_sync()

        result = MyTable.objects().first().run_sync()
        self.assertEqual(result.created_on, created_on)


class TestDateDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_timestamp(self):
        created_on = datetime.datetime.now().date()
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        self.assertEqual(result.created_on, created_on)
