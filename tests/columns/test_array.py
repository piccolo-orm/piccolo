import datetime
from unittest import TestCase

import pytest

from piccolo.columns.column_types import (
    Array,
    BigInt,
    Date,
    Integer,
    Time,
    Timestamp,
    Timestamptz,
)
from piccolo.querystring import QueryString
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_only, engines_skip, sqlite_only


class MyTable(Table):
    value = Array(base_column=Integer())


class TestArrayDefault(TestCase):
    def test_array_default(self):
        """
        We use ``ListProxy`` instead of ``list`` as a default, because of
        issues with Sphinx's autodoc. Make sure it's correctly converted to a
        plain ``list`` in ``Array.__init__``.
        """
        column = Array(base_column=Integer())
        self.assertTrue(column.default is list)


class TestArray(TableTest):
    """
    Make sure an Array column can be created, and works correctly.
    """

    tables = [MyTable]

    @pytest.mark.cockroach_array_slow
    def test_storage(self):
        """
        Make sure data can be stored and retrieved.

        In CockroachDB <= v22.2.0 we had this error:

        * https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        In newer CockroachDB versions, it runs but is very slow:

        * https://github.com/piccolo-orm/piccolo/issues/1005

        """  # noqa: E501
        MyTable(value=[1, 2, 3]).save().run_sync()

        row = MyTable.objects().first().run_sync()
        assert row is not None
        self.assertEqual(row.value, [1, 2, 3])

    @engines_skip("sqlite")
    @pytest.mark.cockroach_array_slow
    def test_index(self):
        """
        Indexes should allow individual array elements to be queried.

        In CockroachDB <= v22.2.0 we had this error:

        * https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        In newer CockroachDB versions, it runs but is very slow:

        * https://github.com/piccolo-orm/piccolo/issues/1005

        """  # noqa: E501
        MyTable(value=[1, 2, 3]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value[0]).first().run_sync(), {"value": 1}
        )

    @engines_skip("sqlite")
    @pytest.mark.cockroach_array_slow
    def test_all(self):
        """
        Make sure rows can be retrieved where all items in an array match a
        given value.

        In CockroachDB <= v22.2.0 we had this error:

        * https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        In newer CockroachDB versions, it runs but is very slow:

        * https://github.com/piccolo-orm/piccolo/issues/1005

        """  # noqa: E501
        MyTable(value=[1, 1, 1]).save().run_sync()

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.all(QueryString("{}::INTEGER", 1)))
            .first()
            .run_sync(),
            {"value": [1, 1, 1]},
        )

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.all(QueryString("{}::INTEGER", 0)))
            .first()
            .run_sync(),
            None,
        )

    @engines_skip("sqlite")
    @pytest.mark.cockroach_array_slow
    def test_any(self):
        """
        Make sure rows can be retrieved where any items in an array match a
        given value.

        In CockroachDB <= v22.2.0 we had this error:

        * https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        In newer CockroachDB versions, it runs but is very slow:

        * https://github.com/piccolo-orm/piccolo/issues/1005

        """  # noqa: E501

        MyTable(value=[1, 2, 3]).save().run_sync()

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.any(QueryString("{}::INTEGER", 1)))
            .first()
            .run_sync(),
            {"value": [1, 2, 3]},
        )

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.any(QueryString("{}::INTEGER", 0)))
            .first()
            .run_sync(),
            None,
        )

    @engines_skip("sqlite")
    @pytest.mark.cockroach_array_slow
    def test_not_any(self):
        """
        Make sure rows can be retrieved where the array doesn't contain a
        certain value.

        In CockroachDB <= v22.2.0 we had this error:

        * https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        In newer CockroachDB versions, it runs but is very slow:

        * https://github.com/piccolo-orm/piccolo/issues/1005

        """  # noqa: E501

        MyTable(value=[1, 2, 3]).save().run_sync()
        MyTable(value=[4, 5, 6]).save().run_sync()

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.not_any(QueryString("{}::INTEGER", 4)))
            .run_sync(),
            [{"value": [1, 2, 3]}],
        )

    @engines_skip("sqlite")
    @pytest.mark.cockroach_array_slow
    def test_cat(self):
        """
        Make sure values can be appended to an array.

        In CockroachDB <= v22.2.0 we had this error:

        * https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        In newer CockroachDB versions, it runs but is very slow:

        * https://github.com/piccolo-orm/piccolo/issues/1005

        """  # noqa: E501
        MyTable(value=[1, 1, 1]).save().run_sync()

        MyTable.update(
            {MyTable.value: MyTable.value.cat([2])}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [1, 1, 1, 2]}],
        )

        # Try plus symbol

        MyTable.update(
            {MyTable.value: MyTable.value + [3]}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [1, 1, 1, 2, 3]}],
        )

        # Make sure non-list values work

        MyTable.update(
            {MyTable.value: MyTable.value + 4}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [1, 1, 1, 2, 3, 4]}],
        )

    @sqlite_only
    def test_cat_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            MyTable.value.cat([2])

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array appending.",
        )


###############################################################################
# Date and time arrays


class DateTimeArrayTable(Table):
    date = Array(Date())
    time = Array(Time())
    timestamp = Array(Timestamp())
    timestamptz = Array(Timestamptz())
    date_nullable = Array(Date(), null=True)
    time_nullable = Array(Time(), null=True)
    timestamp_nullable = Array(Timestamp(), null=True)
    timestamptz_nullable = Array(Timestamptz(), null=True)


class TestDateTimeArray(TestCase):
    """
    Make sure that data can be stored and retrieved when using arrays of
    date / time / timestamp.

    We have to serialise / deserialise it in a special way in SQLite, hence
    the tests.

    """

    def setUp(self):
        DateTimeArrayTable.create_table().run_sync()

    def tearDown(self):
        DateTimeArrayTable.alter().drop_table().run_sync()

    @engines_only("postgres", "sqlite")
    def test_storage(self):
        test_date = datetime.date(year=2024, month=1, day=1)
        test_time = datetime.time(hour=12, minute=0)
        test_timestamp = datetime.datetime(
            year=2024, month=1, day=1, hour=12, minute=0
        )
        test_timestamptz = datetime.datetime(
            year=2024,
            month=1,
            day=1,
            hour=12,
            minute=0,
            tzinfo=datetime.timezone.utc,
        )

        DateTimeArrayTable(
            {
                DateTimeArrayTable.date: [test_date],
                DateTimeArrayTable.time: [test_time],
                DateTimeArrayTable.timestamp: [test_timestamp],
                DateTimeArrayTable.timestamptz: [test_timestamptz],
                DateTimeArrayTable.date_nullable: None,
                DateTimeArrayTable.time_nullable: None,
                DateTimeArrayTable.timestamp_nullable: None,
                DateTimeArrayTable.timestamptz_nullable: None,
            }
        ).save().run_sync()

        row = DateTimeArrayTable.objects().first().run_sync()
        assert row is not None

        self.assertListEqual(row.date, [test_date])
        self.assertListEqual(row.time, [test_time])
        self.assertListEqual(row.timestamp, [test_timestamp])
        self.assertListEqual(row.timestamptz, [test_timestamptz])

        self.assertIsNone(row.date_nullable)
        self.assertIsNone(row.time_nullable)
        self.assertIsNone(row.timestamp_nullable)
        self.assertIsNone(row.timestamptz_nullable)


###############################################################################
# Nested arrays


class NestedArrayTable(Table):
    value = Array(base_column=Array(base_column=BigInt()))


class TestNestedArray(TestCase):
    """
    Make sure that tables with nested arrays can be created, and work
    correctly.

    Related to this bug, with nested array columns containing ``BigInt``:

    https://github.com/piccolo-orm/piccolo/issues/936

    """

    def setUp(self):
        NestedArrayTable.create_table().run_sync()

    def tearDown(self):
        NestedArrayTable.alter().drop_table().run_sync()

    @engines_only("postgres", "sqlite")
    def test_storage(self):
        """
        Make sure data can be stored and retrieved.

        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        """  # noqa: E501
        NestedArrayTable(value=[[1, 2, 3], [4, 5, 6]]).save().run_sync()

        row = NestedArrayTable.objects().first().run_sync()
        assert row is not None
        self.assertEqual(row.value, [[1, 2, 3], [4, 5, 6]])


class TestGetDimensions(TestCase):
    def test_get_dimensions(self):
        """
        Make sure that `_get_dimensions` returns the correct value.
        """
        self.assertEqual(Array(Integer())._get_dimensions(), 1)
        self.assertEqual(Array(Array(Integer()))._get_dimensions(), 2)
        self.assertEqual(Array(Array(Array(Integer())))._get_dimensions(), 3)


class TestGetInnerValueType(TestCase):
    def test_get_inner_value_type(self):
        """
        Make sure that `_get_inner_value_type` returns the correct base type.
        """
        self.assertEqual(Array(Integer())._get_inner_value_type(), int)
        self.assertEqual(Array(Array(Integer()))._get_inner_value_type(), int)
        self.assertEqual(
            Array(Array(Array(Integer())))._get_inner_value_type(), int
        )
