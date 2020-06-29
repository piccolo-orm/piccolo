import datetime
import decimal
from unittest import TestCase
import uuid

from piccolo.columns.column_types import (
    BigInt,
    Date,
    DateDefault,
    ForeignKey,
    Integer,
    Numeric,
    Real,
    SmallInt,
    Text,
    Time,
    TimeDefault,
    Timestamp,
    TimestampDefault,
    UUID,
    UUIDDefault,
    Varchar,
)
from piccolo.table import Table


class TestDefaults(TestCase):
    def test_defaults(self):
        """
        Columns check the type of the default argument.
        """
        for _type in (Integer, BigInt, SmallInt):
            _type(default=0)
            _type(default=None, null=True)
            with self.assertRaises(ValueError):
                _type(default="hello world")
            with self.assertRaises(ValueError):
                _type(default=None, null=False)

        for _type in (Text, Varchar):
            _type(default="")
            _type(default=None, null=True)
            with self.assertRaises(ValueError):
                _type(default=123)
            with self.assertRaises(ValueError):
                _type(default=None, null=False)

        Real(default=0.0)
        Real(default=None, null=True)
        with self.assertRaises(ValueError):
            Real(default="hello world")
        with self.assertRaises(ValueError):
            Real(default=None, null=False)

        Numeric(default=decimal.Decimal(1.0))
        Numeric(default=None, null=True)
        with self.assertRaises(ValueError):
            Numeric(default="hello world")
        with self.assertRaises(ValueError):
            Numeric(default=None, null=False)

        UUID(default=None, null=True)
        UUID(default=UUIDDefault.uuid4)
        UUID(default=uuid.uuid4())
        with self.assertRaises(ValueError):
            UUID(default="hello world")
        with self.assertRaises(ValueError):
            UUID(default=None, null=False)

        Time(default=None, null=True)
        Time(default=TimeDefault.now)
        Time(default=datetime.datetime.now().time())
        with self.assertRaises(ValueError):
            Time(default="hello world")
        with self.assertRaises(ValueError):
            Time(default=None, null=False)

        Date(default=None, null=True)
        Date(default=DateDefault.now)
        Date(default=datetime.datetime.now().date())
        with self.assertRaises(ValueError):
            Date(default="hello world")
        with self.assertRaises(ValueError):
            Date(default=None, null=False)

        Timestamp(default=None, null=True)
        Timestamp(default=TimestampDefault.now)
        Timestamp(default=datetime.datetime.now())
        with self.assertRaises(ValueError):
            Timestamp(default="hello world")
        with self.assertRaises(ValueError):
            Timestamp(default=None, null=False)

        ForeignKey(references=Table(), default=None, null=True)
        ForeignKey(references=Table(), default=1)
        with self.assertRaises(ValueError):
            ForeignKey(references=Table, default="hello world")
        with self.assertRaises(ValueError):
            ForeignKey(references=Table, default=None, null=False)
