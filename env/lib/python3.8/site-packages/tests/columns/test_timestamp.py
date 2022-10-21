import datetime
from unittest import TestCase

from piccolo.columns.column_types import Timestamp
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.table import Table


class MyTable(Table):
    created_on = Timestamp()


class MyTableDefault(Table):
    """
    A table containing all of the possible `default` arguments for
    `Timestamp`.
    """

    created_on = Timestamp(default=TimestampNow())


class TestTimestamp(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_timestamp(self):
        """
        Make sure a datetime can be stored and retrieved.
        """
        created_on = datetime.datetime.now()
        row = MyTable(created_on=created_on)
        row.save().run_sync()

        result = MyTable.objects().first().run_sync()
        self.assertEqual(result.created_on, created_on)

    def test_timezone_aware(self):
        """
        Raise an error if a timezone aware datetime is given as a default.
        """
        with self.assertRaises(ValueError):
            Timestamp(default=datetime.datetime.now(tz=datetime.timezone.utc))


class TestTimestampDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_timestamp(self):
        """
        Make sure the default values get created correctly.
        """
        created_on = datetime.datetime.now()
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        self.assertLess(
            result.created_on - created_on, datetime.timedelta(seconds=1)
        )
        self.assertIsNone(result.created_on.tzinfo)
