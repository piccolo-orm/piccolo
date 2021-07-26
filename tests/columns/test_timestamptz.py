import datetime
from unittest import TestCase

from dateutil import tz

from piccolo.columns.column_types import Timestamptz
from piccolo.columns.defaults.timestamptz import (
    TimestamptzCustom,
    TimestamptzNow,
    TimestamptzOffset,
)
from piccolo.table import Table


class MyTable(Table):
    created_on = Timestamptz()


class MyTableDefault(Table):
    """
    A table containing all of the possible `default` arguments for
    `Timestamptz`.
    """

    created_on = Timestamptz(default=TimestamptzNow())
    created_on_offset = Timestamptz(default=TimestamptzOffset(days=1))
    created_on_custom = Timestamptz(default=TimestamptzCustom(year=2021))
    created_on_datetime = Timestamptz(
        default=datetime.datetime(year=2020, month=1, day=1)
    )


class CustomTimezone(datetime.tzinfo):
    pass


class TestTimestamptz(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_timestamptz_timezone_aware(self):
        """
        Test storing a timezone aware timestamp.
        """
        for tzinfo in (
            datetime.timezone.utc,
            tz.gettz("America/New_York"),
        ):
            created_on = datetime.datetime(
                year=2020,
                month=1,
                day=1,
                hour=12,
                minute=0,
                second=0,
                tzinfo=tzinfo,
            )
            row = MyTable(created_on=created_on)
            row.save().run_sync()

            # Fetch it back from the database
            result = (
                MyTable.objects()
                .where(
                    MyTable._meta.primary_key
                    == getattr(row, MyTable._meta.primary_key._meta.name)
                )
                .first()
                .run_sync()
            )
            self.assertEqual(result.created_on, created_on)

            # The database converts it to UTC
            self.assertEqual(result.created_on.tzinfo, datetime.timezone.utc)


class TestTimestamptzDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_timestamptz_default(self):
        """
        Make sure the default value gets created, and can be retrieved.
        """
        created_on = datetime.datetime.now(tz=datetime.timezone.utc)
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        delta = result.created_on - created_on
        self.assertTrue(delta < datetime.timedelta(seconds=1))
        self.assertEqual(result.created_on.tzinfo, datetime.timezone.utc)
