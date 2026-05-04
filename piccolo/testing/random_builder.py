import datetime
import decimal
import enum
import random
import string
import uuid
from typing import Any


class RandomBuilder:
    @classmethod
    def next_bool(cls) -> bool:
        return random.choice([True, False])

    @classmethod
    def next_bytes(cls, length=8) -> bytes:
        return random.getrandbits(length * 8).to_bytes(length, "little")

    @classmethod
    def next_date(cls) -> datetime.date:
        return datetime.date(
            year=random.randint(2000, 2050),
            month=random.randint(1, 12),
            day=random.randint(1, 28),
        )

    @classmethod
    def next_datetime(cls, tz_aware: bool = False) -> datetime.datetime:
        return datetime.datetime(
            year=random.randint(2000, 2050),
            month=random.randint(1, 12),
            day=random.randint(1, 28),
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
            tzinfo=datetime.timezone.utc if tz_aware else None,
        )

    @classmethod
    def next_enum(cls, e: type[enum.Enum]) -> Any:
        return random.choice([item.value for item in e])

    @classmethod
    def next_float(cls, minimum=0, maximum=2147483647, scale=5) -> float:
        return round(random.uniform(minimum, maximum), scale)

    @classmethod
    def next_decimal(
        cls, precision: int = 4, scale: int = 2
    ) -> decimal.Decimal:
        # For precision 4 and scale 2, maximum needs to be 99.99.
        maximum = (10 ** (precision - scale)) - (10 ** (-1 * scale))
        float_number = cls.next_float(maximum=maximum, scale=scale)
        # We convert float_number to a string first, otherwise the decimal
        # value is slightly off due to floating point precision.
        return decimal.Decimal(str(float_number))

    @classmethod
    def next_int(cls, minimum=0, maximum=2147483647) -> int:
        return random.randint(minimum, maximum)

    @classmethod
    def next_str(cls, length=16) -> str:
        return "".join(
            random.choice(string.ascii_letters) for _ in range(length)
        )

    @classmethod
    def next_time(cls) -> datetime.time:
        return datetime.time(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )

    @classmethod
    def next_timedelta(cls) -> datetime.timedelta:
        return datetime.timedelta(
            days=random.randint(1, 7),
            hours=random.randint(1, 23),
            minutes=random.randint(0, 59),
        )

    @classmethod
    def next_uuid(cls) -> uuid.UUID:
        return uuid.uuid4()
