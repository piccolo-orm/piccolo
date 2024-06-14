import datetime

from piccolo.columns import Timestamp
from piccolo.query.functions.datetime import (
    Day,
    Extract,
    Hour,
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
        Concert(
            {
                Concert.starts: datetime.datetime(
                    year=2024, month=6, day=14, hour=23, minute=46, second=10
                )
            }
        ).save().run_sync()


class TestDay(DatetimeTest):
    def test_day(self):
        self.assertEqual(
            Concert.select(Day(Concert.starts, alias="starts_day")).run_sync(),
            [{"starts_day": 14}],
        )
