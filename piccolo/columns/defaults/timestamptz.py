from __future__ import annotations

import datetime as pydatetime
import typing as t
from enum import Enum

try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore  # noqa: F401

from .timestamp import TimestampCustom, TimestampNow, TimestampOffset


class TimestamptzOffset(TimestampOffset):
    def __init__(
        self,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        tz: ZoneInfo = ZoneInfo("UTC"),
    ):
        self.tz = tz
        super().__init__(
            days=days, hours=hours, minutes=minutes, seconds=seconds
        )

    @property
    def cockroach(self):
        interval_string = self.get_postgres_interval_string(
            ["days", "hours", "minutes", "seconds"]
        )
        return f"CURRENT_TIMESTAMP + INTERVAL '{interval_string}'"

    def python(self):
        return pydatetime.datetime.now(tz=self.tz) + pydatetime.timedelta(
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
        )


class TimestamptzNow(TimestampNow):
    def __init__(self, tz: ZoneInfo = ZoneInfo("UTC")):
        self.tz = tz

    @property
    def cockroach(self):
        return "current_timestamp"

    def python(self):
        return pydatetime.datetime.now(tz=self.tz)


class TimestamptzCustom(TimestampCustom):
    def __init__(
        self,
        year: int = 2000,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
        second: int = 0,
        microsecond: int = 0,
        tz: ZoneInfo = ZoneInfo("UTC"),
    ):
        self.tz = tz
        super().__init__(
            year=year,
            month=month,
            day=day,
            hour=hour,
            second=second,
            microsecond=microsecond,
        )

    @property
    def cockroach(self):
        return "'{}'".format(self.datetime.isoformat().replace("T", " "))

    @property
    def datetime(self):
        return pydatetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            second=self.second,
            microsecond=self.microsecond,
            tzinfo=self.tz,
        )

    @classmethod
    def from_datetime(
        cls, instance: pydatetime.datetime, tz: ZoneInfo = ZoneInfo("UTC")
    ):  # type: ignore
        if instance.tzinfo is not None:
            instance = instance.astimezone(tz)
        return cls(
            year=instance.year,
            month=instance.month,
            day=instance.month,
            hour=instance.hour,
            second=instance.second,
            microsecond=instance.microsecond,
        )


TimestamptzArg = t.Union[
    TimestamptzCustom,
    TimestamptzNow,
    TimestamptzOffset,
    Enum,
    None,
    pydatetime.datetime,
]


__all__ = [
    "TimestamptzArg",
    "TimestamptzCustom",
    "TimestamptzNow",
    "TimestamptzOffset",
]
