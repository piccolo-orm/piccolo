from __future__ import annotations

import datetime
import typing as t
from enum import Enum
from zoneinfo import ZoneInfo

from .timestamp import TimestampCustom, TimestampNow, TimestampOffset


class TimestamptzOffset(TimestampOffset):
    @property
    def cockroach(self):
        interval_string = self.get_postgres_interval_string(
            ["days", "hours", "minutes", "seconds"]
        )
        return f"CURRENT_TIMESTAMP + INTERVAL '{interval_string}'"

    def python(self):
        return datetime.datetime.now(
            tz=datetime.timezone.utc
        ) + datetime.timedelta(
            days=self.days,
            hours=self.hours,
            minutes=self.minutes,
            seconds=self.seconds,
        )


class TimestamptzNow(TimestampNow):
    def __init__(self, tz: ZoneInfo = ZoneInfo('UTC')):
        self._tz = tz
        
    @property
    def cockroach(self):
        return "current_timestamp"

    def python(self):
        return datetime.datetime.now(tz=self._tz)


class TimestamptzCustom(TimestampCustom):
    @property
    def cockroach(self):
        return "'{}'".format(self.datetime.isoformat().replace("T", " "))

    @property
    def datetime(self):
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            second=self.second,
            microsecond=self.microsecond,
            tzinfo=datetime.timezone.utc,
        )

    @classmethod
    def from_datetime(cls, instance: datetime.datetime):  # type: ignore
        if instance.tzinfo is not None:
            instance = instance.astimezone(datetime.timezone.utc)
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
    datetime.datetime,
]


__all__ = [
    "TimestamptzArg",
    "TimestamptzCustom",
    "TimestamptzNow",
    "TimestamptzOffset",
]
