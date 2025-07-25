from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum
from typing import Union

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
    @property
    def cockroach(self):
        return "current_timestamp"

    def python(self):
        return datetime.datetime.now(tz=datetime.timezone.utc)


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
            minute=self.minute,
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
            day=instance.day,
            hour=instance.hour,
            minute=instance.minute,
            second=instance.second,
            microsecond=instance.microsecond,
        )


TimestamptzArg = Union[
    TimestamptzCustom,
    TimestamptzNow,
    TimestamptzOffset,
    Enum,
    None,
    datetime.datetime,
    Callable[[], datetime.datetime],
]


__all__ = [
    "TimestamptzArg",
    "TimestamptzCustom",
    "TimestamptzNow",
    "TimestamptzOffset",
]
