import datetime
from decimal import Decimal
from unittest import TestCase

from piccolo.columns.column_types import (
    Array,
    BigInt,
    Date,
    Integer,
    Numeric,
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

    @engines_skip("mysql")
    def test_storage(self):
        """
        Make sure data can be stored and retrieved.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()

        row = MyTable.objects().first().run_sync()
        assert row is not None
        self.assertEqual(row.value, [1, 2, 3])

    @engines_only("mysql")
    def test_storage_mysql(self):
        MyTable(value=[1, 2, 3]).save().run_sync()

        row = MyTable.objects().first().run_sync()
        assert row is not None
        self.assertEqual(row.value, "[1, 2, 3]")

    @engines_skip("sqlite", "mysql")
    def test_index(self):
        """
        Indexes should allow individual array elements to be queried.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value[0]).first().run_sync(), {"value": 1}
        )

    @engines_skip("sqlite", "mysql")
    def test_all(self):
        """
        Make sure rows can be retrieved where all items in an array match a
        given value.
        """
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

    @engines_only("mysql")
    def test_all_mysql(self):
        MyTable(value=[1, 1, 1]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.all(QueryString("{}", 1)))
            .first()
            .run_sync(),
            {"value": "[1, 1, 1]"},
        )

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.all(QueryString("{}", 0)))
            .first()
            .run_sync(),
            None,
        )

    @engines_skip("sqlite", "mysql")
    def test_any(self):
        """
        Make sure rows can be retrieved where any items in an array match a
        given value.
        """
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

    @engines_only("mysql")
    def test_any_mysql(self):
        MyTable(value=[1, 2, 3]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.any(QueryString("{}", 1)))
            .first()
            .run_sync(),
            {"value": "[1, 2, 3]"},
        )

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.any(QueryString("{}", 4)))
            .first()
            .run_sync(),
            None,
        )

    @engines_skip("sqlite", "mysql")
    def test_not_any(self):
        """
        Make sure rows can be retrieved where the array doesn't contain a
        certain value.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()
        MyTable(value=[4, 5, 6]).save().run_sync()

        # We have to explicitly specify the type, so CockroachDB works.
        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.not_any(QueryString("{}::INTEGER", 4)))
            .run_sync(),
            [{"value": [1, 2, 3]}],
        )

    @engines_only("mysql")
    def test_not_any_mysql(self):
        MyTable(value=[1, 2, 3]).save().run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.not_any(QueryString("{}", 4)))
            .first()
            .run_sync(),
            {"value": "[1, 2, 3]"},
        )

        self.assertEqual(
            MyTable.select(MyTable.value)
            .where(MyTable.value.not_any(QueryString("{}", 1)))
            .first()
            .run_sync(),
            None,
        )

    @engines_skip("sqlite", "mysql")
    def test_cat(self):
        """
        Make sure values can be appended to an array and that we can
        concatenate two arrays.
        """
        MyTable(value=[5]).save().run_sync()

        MyTable.update(
            {MyTable.value: MyTable.value.cat([6])}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [5, 6]}],
        )

        # Try plus symbol - add array to the end

        MyTable.update(
            {MyTable.value: MyTable.value + [7]}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [5, 6, 7]}],
        )

        # Add array to the start

        MyTable.update(
            {MyTable.value: [4] + MyTable.value}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [4, 5, 6, 7]}],
        )

        # Add array to the start and end
        MyTable.update(
            {MyTable.value: [3] + MyTable.value + [8]}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [3, 4, 5, 6, 7, 8]}],
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
            "Only Postgres and Cockroach support array concatenation.",
        )

    @engines_skip("sqlite", "mysql")
    def test_prepend(self):
        """
        Make sure values can be added to the beginning of the array.
        """
        MyTable(value=[1, 1, 1]).save().run_sync()

        MyTable.update(
            {MyTable.value: MyTable.value.prepend(3)}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [3, 1, 1, 1]}],
        )

    @sqlite_only
    def test_prepend_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            MyTable.value.prepend(2)

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array prepending.",
        )

    @engines_skip("sqlite", "mysql")
    def test_append(self):
        """
        Make sure values can be appended to an array.
        """
        MyTable(value=[1, 1, 1]).save().run_sync()

        MyTable.update(
            {MyTable.value: MyTable.value.append(3)}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [1, 1, 1, 3]}],
        )

    @sqlite_only
    def test_append_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            MyTable.value.append(2)

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array appending.",
        )

    @engines_skip("sqlite", "mysql")
    def test_replace(self):
        """
        Make sure values can be swapped in the array.
        """
        MyTable(value=[1, 1, 1]).save().run_sync()

        MyTable.update(
            {MyTable.value: MyTable.value.replace(1, 2)}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [2, 2, 2]}],
        )

    @sqlite_only
    def test_replace_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            MyTable.value.replace(1, 2)

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array substitution.",
        )

    @engines_skip("sqlite", "mysql")
    def test_remove(self):
        """
        Make sure values can be removed from an array.
        """
        MyTable(value=[1, 2, 3]).save().run_sync()

        MyTable.update(
            {MyTable.value: MyTable.value.remove(2)}, force=True
        ).run_sync()

        self.assertEqual(
            MyTable.select(MyTable.value).run_sync(),
            [{"value": [1, 3]}],
        )

    @sqlite_only
    def test_remove_sqlite(self):
        """
        If using SQLite then an exception should be raised currently.
        """
        with self.assertRaises(ValueError) as manager:
            MyTable.value.remove(2)

        self.assertEqual(
            str(manager.exception),
            "Only Postgres and Cockroach support array removing.",
        )


###############################################################################
# Date, time and decimal arrays


class DateTimeDecimalArrayTable(Table):
    date = Array(Date())
    time = Array(Time())
    timestamp = Array(Timestamp())
    timestamptz = Array(Timestamptz())
    decimal = Array(Numeric(digits=(5, 2)))
    date_nullable = Array(Date(), null=True)
    time_nullable = Array(Time(), null=True)
    timestamp_nullable = Array(Timestamp(), null=True)
    timestamptz_nullable = Array(Timestamptz(), null=True)
    decimal_nullable = Array(Numeric(digits=(5, 2)), null=True)


@engines_skip("mysql")
class TestDateTimeDecimalArray(TestCase):
    """
    Make sure that data can be stored and retrieved when using arrays of
    date / time / timestamp.

    We have to serialise / deserialise it in a special way in SQLite, hence
    the tests.

    """

    def setUp(self):
        DateTimeDecimalArrayTable.create_table().run_sync()

    def tearDown(self):
        DateTimeDecimalArrayTable.alter().drop_table().run_sync()

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
        test_decimal = Decimal("50.0")

        DateTimeDecimalArrayTable(
            {
                DateTimeDecimalArrayTable.date: [test_date],
                DateTimeDecimalArrayTable.time: [test_time],
                DateTimeDecimalArrayTable.timestamp: [test_timestamp],
                DateTimeDecimalArrayTable.timestamptz: [test_timestamptz],
                DateTimeDecimalArrayTable.decimal: [test_decimal],
                DateTimeDecimalArrayTable.date_nullable: None,
                DateTimeDecimalArrayTable.time_nullable: None,
                DateTimeDecimalArrayTable.timestamp_nullable: None,
                DateTimeDecimalArrayTable.timestamptz_nullable: None,
                DateTimeDecimalArrayTable.decimal_nullable: None,
            }
        ).save().run_sync()

        row = DateTimeDecimalArrayTable.objects().first().run_sync()
        assert row is not None

        self.assertListEqual(row.date, [test_date])
        self.assertListEqual(row.time, [test_time])
        self.assertListEqual(row.timestamp, [test_timestamp])
        self.assertListEqual(row.timestamptz, [test_timestamptz])
        self.assertListEqual(row.decimal, [test_decimal])

        self.assertIsNone(row.date_nullable)
        self.assertIsNone(row.time_nullable)
        self.assertIsNone(row.timestamp_nullable)
        self.assertIsNone(row.timestamptz_nullable)
        self.assertIsNone(row.decimal_nullable)


###############################################################################
# Nested arrays


class NestedArrayTable(Table):
    value = Array(base_column=Array(base_column=BigInt()))


@engines_skip("mysql")
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

        🐛 Cockroach bug: https://go.crdb.dev/issue-v/32552/v25.4
        asyncpg.exceptions.FeatureNotSupportedError
        """
        NestedArrayTable(value=[[1, 2, 3], [4, 5, 6]]).save().run_sync()

        row = NestedArrayTable.objects().first().run_sync()
        assert row is not None
        self.assertEqual(row.value, [[1, 2, 3], [4, 5, 6]])


@engines_skip("mysql")
class TestGetDimensions(TestCase):
    def test_get_dimensions(self):
        """
        Make sure that `_get_dimensions` returns the correct value.
        """
        self.assertEqual(Array(Integer())._get_dimensions(), 1)
        self.assertEqual(Array(Array(Integer()))._get_dimensions(), 2)
        self.assertEqual(Array(Array(Array(Integer())))._get_dimensions(), 3)


@engines_skip("mysql")
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
