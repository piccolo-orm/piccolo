import datetime
from unittest import TestCase

from piccolo.table import Table
from piccolo.columns.column_types import Timestamp
from piccolo.columns.defaults.timestamp import TimestampNow


class MyTable(Table):
    created_on = Timestamp()


class MyTableDefault(Table):
    created_on = Timestamp(default=TimestampNow())


class TestTimestamp(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_timestamp(self):
        created_on = datetime.datetime.now()
        row = MyTable(created_on=created_on)
        row.save().run_sync()

        result = MyTable.objects().first().run_sync()
        self.assertEqual(result.created_on, created_on)


class TestTimestampDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_timestamp(self):
        created_on = datetime.datetime.now()
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        self.assertTrue(
            result.created_on - created_on < datetime.timedelta(seconds=1)
        )
