import datetime
import decimal
import enum
import random
import string
import typing as t
import uuid


class RandomBuilder:
    @classmethod
    def get_mapper(cls) -> t.Dict[t.Type, t.Callable]:
        """
        This is the public API for users to get the
        provided random mapper.

        """
        return {
            bool: cls.next_bool,
            bytes: cls.next_bytes,
            datetime.date: cls.next_date,
            datetime.datetime: cls.next_datetime,
            float: cls.next_float,
            decimal.Decimal: cls.next_decimal,
            int: cls.next_int,
            str: cls.next_str,
            datetime.time: cls.next_time,
            datetime.timedelta: cls.next_timedelta,
            uuid.UUID: cls.next_uuid,
        }

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
    def next_enum(cls, e: t.Type[enum.Enum]) -> t.Any:
        return random.choice([item.value for item in e])

    @classmethod
    def next_float(cls, minimum=0, maximum=2147483647, scale=5) -> float:
        return round(random.uniform(minimum, maximum), scale)

    @classmethod
    def next_decimal(
        cls, precision: int = 4, scale: int = 2
    ) -> decimal.Decimal:
        float_number = cls.next_float(
            maximum=10 ** (precision - scale), scale=scale
        )
        return decimal.Decimal(str(float_number))

    @classmethod
    def next_int(cls, minimum=0, maximum=2147483647) -> int:
        return random.randint(minimum, maximum)

    @classmethod
    def next_str(cls, length: int = 16) -> str:
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

    @classmethod
    def next_list(cls, callable_: t.Callable) -> t.List[t.Any]:
        length = cls.next_int(maximum=10)
        return [callable_() for _ in range(length)]
