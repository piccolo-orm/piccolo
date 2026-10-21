import datetime

from piccolo.columns.column_types import Interval
from piccolo.columns.defaults.interval import IntervalCustom
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTable(Table):
    interval = Interval()


class MyTableDefault(Table):
    interval = Interval(default=IntervalCustom(days=1))


class TestInterval(TableTest):
    tables = [MyTable]

    def test_interval(self):
        # Test a range of different timedeltas
        intervals = [
            datetime.timedelta(weeks=1),
            datetime.timedelta(days=1),
            datetime.timedelta(hours=1),
            datetime.timedelta(minutes=1),
            datetime.timedelta(seconds=1),
            datetime.timedelta(milliseconds=1),
            datetime.timedelta(microseconds=1),
        ]

        for interval in intervals:
            # Make sure that saving it works OK.
            row = MyTable(interval=interval)
            row.save().run_sync()

            # Make sure that fetching it back works OK.
            result = (
                MyTable.objects()
                .where(
                    MyTable._meta.primary_key
                    == getattr(row, MyTable._meta.primary_key._meta.name)
                )
                .first()
                .run_sync()
            )
            assert result is not None
            self.assertEqual(result.interval, interval)

    def test_interval_where_clause(self):
        """
        Make sure a range of where clauses resolve correctly.
        """
        interval = datetime.timedelta(hours=2)
        row = MyTable(interval=interval)
        row.save().run_sync()

        result = (
            MyTable.objects()
            .where(MyTable.interval < datetime.timedelta(hours=3))
            .first()
            .run_sync()
        )
        self.assertIsNotNone(result)

        result = (
            MyTable.objects()
            .where(MyTable.interval < datetime.timedelta(days=1))
            .first()
            .run_sync()
        )
        self.assertIsNotNone(result)

        result = (
            MyTable.objects()
            .where(MyTable.interval > datetime.timedelta(minutes=1))
            .first()
            .run_sync()
        )
        self.assertIsNotNone(result)

        result = (
            MyTable.exists()
            .where(MyTable.interval == datetime.timedelta(hours=2))
            .run_sync()
        )
        self.assertTrue(result)


class TestIntervalDefault(TableTest):
    tables = [MyTableDefault]

    def test_interval(self):
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        assert result is not None
        self.assertEqual(result.interval.days, 1)
