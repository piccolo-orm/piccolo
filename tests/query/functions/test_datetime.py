import datetime

from piccolo.columns import Timestamp
from piccolo.query.functions.datetime import (
    Day,
    Extract,
    Hour,
    Minute,
    Month,
    Second,
    Strftime,
    Year,
)
from piccolo.table import Table

from .base import FunctionTest


class Concert(Table):
    starts = Timestamp()


class DatetimeTest(FunctionTest):
    tables = [Concert]

    def setUp(self) -> None:
        super().setUp()
        self.concert = Concert(
            {
                Concert.starts: datetime.datetime(
                    year=2024, month=6, day=14, hour=23, minute=46, second=10
                )
            }
        )
        self.concert.save().run_sync()


class TestDatabaseAgnostic(DatetimeTest):
    def test_year(self):
        self.assertEqual(
            Concert.select(
                Year(Concert.starts, alias="starts_year")
            ).run_sync(),
            [{"starts_year": self.concert.starts.year}],
        )

    def test_month(self):
        self.assertEqual(
            Concert.select(
                Month(Concert.starts, alias="starts_month")
            ).run_sync(),
            [{"starts_month": self.concert.starts.month}],
        )

    def test_day(self):
        self.assertEqual(
            Concert.select(Day(Concert.starts, alias="starts_day")).run_sync(),
            [{"starts_day": self.concert.starts.day}],
        )

    def test_hour(self):
        self.assertEqual(
            Concert.select(
                Hour(Concert.starts, alias="starts_hour")
            ).run_sync(),
            [{"starts_hour": self.concert.starts.hour}],
        )

    def test_minute(self):
        self.assertEqual(
            Concert.select(
                Minute(Concert.starts, alias="starts_minute")
            ).run_sync(),
            [{"starts_minute": self.concert.starts.minute}],
        )

    def test_second(self):
        self.assertEqual(
            Concert.select(
                Second(Concert.starts, alias="starts_second")
            ).run_sync(),
            [{"starts_second": self.concert.starts.second}],
        )
