import datetime
import time
from operator import eq
from unittest import TestCase

from piccolo.columns.column_types import Timestamptz
from piccolo.columns.defaults.timestamptz import (
    TimestamptzCustom,
    TimestamptzNow,
    TimestamptzOffset,
)
from piccolo.table import Table

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore  # noqa: F401


UTC_TZ = ZoneInfo("UTC")
LOCAL_TZ = ZoneInfo("Europe/Tallinn")


class MyTable(Table):
    created_on_utc = Timestamptz(tz=UTC_TZ)
    created_on_local = Timestamptz(tz=LOCAL_TZ)


class MyTableDefault(Table):
    """
    A table containing all of the possible `default` arguments for
    `Timestamptz`.
    """

    created_on = Timestamptz(default=TimestamptzNow(tz=LOCAL_TZ), tz=LOCAL_TZ)
    created_on_offset = Timestamptz(
        default=TimestamptzOffset(days=1, tz=LOCAL_TZ), tz=LOCAL_TZ
    )
    created_on_custom = Timestamptz(
        default=TimestamptzCustom(year=2021, tz=LOCAL_TZ), tz=LOCAL_TZ
    )
    created_on_datetime = Timestamptz(
        default=datetime.datetime(year=2020, month=1, day=1, tzinfo=LOCAL_TZ),
        tz=LOCAL_TZ,
    )


class TestTimestamptz(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    def test_timestamptz_timezone_aware(self):
        """
        Test storing a timezone aware timestamp.
        """
        dt_args = dict(year=2020, month=1, day=1, hour=12, minute=0, second=0)
        created_on_utc = datetime.datetime(**dt_args, tzinfo=ZoneInfo("UTC"))
        created_on_local = datetime.datetime(
            **dt_args, tzinfo=ZoneInfo("Europe/Tallinn")
        )
        row = MyTable(
            created_on_utc=created_on_utc, created_on_local=created_on_local
        )
        row.save().run_sync()

        # Fetch it back from the database
        p_key = MyTable._meta.primary_key
        p_key_name = getattr(row, p_key._meta.name)
        result = (
            MyTable.objects().where(eq(p_key, p_key_name)).first().run_sync()
        )
        assert result is not None
        self.assertEqual(result.created_on_utc, created_on_utc)
        self.assertEqual(result.created_on_local, created_on_local)

        # The database stores the datetime of the column in UTC timezone, but
        # the column converts it back to the timezone that is defined for it.
        self.assertEqual(result.created_on_utc.tzinfo, created_on_utc.tzinfo)
        self.assertEqual(
            result.created_on_local.tzinfo, created_on_local.tzinfo
        )


class TestTimestamptzDefault(TestCase):
    def setUp(self):
        MyTableDefault.create_table().run_sync()

    def tearDown(self):
        MyTableDefault.alter().drop_table().run_sync()

    def test_timestamptz_default(self):
        """
        Make sure the default value gets created, and can be retrieved.
        """
        created_on = datetime.datetime.now(tz=LOCAL_TZ)
        time.sleep(1e-5)

        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        assert result is not None

        delta = result.created_on - created_on
        self.assertLess(delta, datetime.timedelta(seconds=1))
        self.assertEqual(result.created_on.tzinfo, created_on.tzinfo)

        delta = result.created_on_offset - created_on
        self.assertGreaterEqual(delta, datetime.timedelta(days=1))
        self.assertEqual(result.created_on_offset.tzinfo, created_on.tzinfo)

        delta = created_on - result.created_on_custom
        self.assertGreaterEqual(delta, datetime.timedelta(days=delta.days))
        self.assertEqual(result.created_on_custom.tzinfo, created_on.tzinfo)

        delta = created_on - result.created_on_datetime
        self.assertGreaterEqual(delta, datetime.timedelta(days=delta.days))
        self.assertEqual(result.created_on_datetime.tzinfo, created_on.tzinfo)
