import datetime
import decimal
import uuid
from unittest import TestCase

from piccolo.columns.column_types import (
    UUID,
    UUID4,
    BigInt,
    Date,
    DateNow,
    DoublePrecision,
    ForeignKey,
    Integer,
    Numeric,
    Real,
    SmallInt,
    Text,
    Time,
    TimeNow,
    Timestamp,
    TimestampNow,
    Varchar,
)
from piccolo.table import Table


class TestDefaults(TestCase):
    """
    Columns check the type of the default argument.
    """

    def test_int(self):
        for _type in (Integer, BigInt, SmallInt):
            _type(default=0)
            _type(default=None, null=True)
            with self.assertRaises(ValueError):
                _type(default="hello world")

    def test_text(self):
        for _type in (Text, Varchar):
            _type(default="")
            _type(default=None, null=True)
            with self.assertRaises(ValueError):
                _type(default=123)

    def test_real(self):
        Real(default=0.0)
        Real(default=None, null=True)
        with self.assertRaises(ValueError):
            Real(default="hello world")

    def test_double_precision(self):
        DoublePrecision(default=0.0)
        DoublePrecision(default=None, null=True)
        with self.assertRaises(ValueError):
            DoublePrecision(default="hello world")

    def test_numeric(self):
        Numeric(default=decimal.Decimal(1.0))
        Numeric(default=None, null=True)
        with self.assertRaises(ValueError):
            Numeric(default="hello world")

    def test_uuid(self):
        UUID(default=None, null=True)
        UUID(default=UUID4())
        UUID(default=uuid.uuid4())
        with self.assertRaises(ValueError):
            UUID(default="hello world")

    def test_time(self):
        Time(default=None, null=True)
        Time(default=TimeNow())
        Time(default=datetime.datetime.now().time())
        with self.assertRaises(ValueError):
            Time(default="hello world")

    def test_date(self):
        Date(default=None, null=True)
        Date(default=DateNow())
        Date(default=datetime.datetime.now().date())
        with self.assertRaises(ValueError):
            Date(default="hello world")

    def test_timestamp(self):
        Timestamp(default=None, null=True)
        Timestamp(default=TimestampNow())
        Timestamp(default=datetime.datetime.now())
        with self.assertRaises(ValueError):
            Timestamp(default="hello world")

    def test_foreignkey(self):
        class MyTable(Table):
            pass

        ForeignKey(references=MyTable, default=None, null=True)
        ForeignKey(references=MyTable, default=1)
        with self.assertRaises(ValueError):
            ForeignKey(references=MyTable, default="hello world")
