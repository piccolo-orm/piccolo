import datetime

from piccolo.columns.column_types import Timestamp
from piccolo.columns.defaults.timestamp import TimestampNow
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTable(Table):
    created_on = Timestamp()


class MyTableDefault(Table):
    """
    A table containing all of the possible `default` arguments for
    `Timestamp`.
    """

    created_on = Timestamp(default=TimestampNow())


class TestTimestamp(TableTest):
    tables = [MyTable]

    def test_timestamp(self):
        """
        Make sure a datetime can be stored and retrieved.
        """
        created_on = datetime.datetime.now()
        row = MyTable(created_on=created_on)
        row.save().run_sync()

        result = MyTable.objects().first().run_sync()
        assert result is not None
        self.assertEqual(result.created_on, created_on)

    def test_timezone_aware(self):
        """
        Raise an error if a timezone aware datetime is given as a default.
        """
        with self.assertRaises(ValueError):
            Timestamp(default=datetime.datetime.now(tz=datetime.timezone.utc))


class TestTimestampDefault(TableTest):
    tables = [MyTableDefault]

    def test_timestamp(self):
        """
        Make sure the default values get created correctly.
        """
        created_on = datetime.datetime.now()
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        assert result is not None
        self.assertLess(
            result.created_on - created_on, datetime.timedelta(seconds=1)
        )
        self.assertIsNone(result.created_on.tzinfo)
