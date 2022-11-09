import dataclasses
import datetime
import typing as t
from unittest import TestCase

import pytest

from piccolo.columns.base import Column
from piccolo.columns.column_types import (
    Date,
    Integer,
    Interval,
    Text,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.querystring import QueryString
from piccolo.table import Table
from tests.base import (
    DBTestCase,
    engine_version_lt,
    engines_skip,
    is_running_sqlite,
    sqlite_only,
)
from tests.example_apps.music.tables import Band


class TestUpdate(DBTestCase):
    def check_response(self):
        response = (
            Band.select(Band.name)
            .where(Band.name == "Pythonistas3")
            .run_sync()
        )

        self.assertEqual(response, [{"name": "Pythonistas3"}])

    def test_update(self):
        """
        Make sure updating work, when passing the new values directly to the
        `update` method.
        """
        self.insert_rows()

        Band.update({Band.name: "Pythonistas3"}).where(
            Band.name == "Pythonistas"
        ).run_sync()

        self.check_response()

    def test_update_with_string_keys(self):
        """
        Make sure updating work, when passing a dictionary of values, which
        uses column names as keys, instead of Column instances.
        """
        self.insert_rows()

        Band.update({"name": "Pythonistas3"}).where(
            Band.name == "Pythonistas"
        ).run_sync()

        self.check_response()

    def test_update_with_kwargs(self):
        """
        Make sure updating work, when passing the new value via kwargs.
        """
        self.insert_rows()

        Band.update(name="Pythonistas3").where(
            Band.name == "Pythonistas"
        ).run_sync()

        self.check_response()

    def test_update_values(self):
        """
        Make sure updating work, when passing the new values via the `values`
        method.
        """
        self.insert_rows()

        Band.update().values({Band.name: "Pythonistas3"}).where(
            Band.name == "Pythonistas"
        ).run_sync()

        self.check_response()

    def test_update_values_with_string_keys(self):
        """
        Make sure updating work, when passing the new values via the `values`
        method, using a column name as a dictionary key.
        """
        self.insert_rows()

        Band.update().values({"name": "Pythonistas3"}).where(
            Band.name == "Pythonistas"
        ).run_sync()

        self.check_response()

    def test_update_values_with_kwargs(self):
        """
        Make sure updating work, when passing the new values via kwargs.
        """
        self.insert_rows()

        Band.update().values(name="Pythonistas3").where(
            Band.name == "Pythonistas"
        ).run_sync()

        self.check_response()

    @pytest.mark.skipif(
        is_running_sqlite() and engine_version_lt(3.35),
        reason="SQLite version not supported",
    )
    def test_update_returning(self):
        """
        Make sure update works with the `returning` clause.
        """
        self.insert_rows()

        response = (
            Band.update({Band.name: "Pythonistas 2"})
            .where(Band.name == "Pythonistas")
            .returning(Band.name)
            .run_sync()
        )

        self.assertEqual(response, [{"name": "Pythonistas 2"}])

    @pytest.mark.skipif(
        is_running_sqlite() and engine_version_lt(3.35),
        reason="SQLite version not supported",
    )
    def test_update_returning_alias(self):
        """
        Make sure update works with the `returning` clause.
        """
        self.insert_rows()

        response = (
            Band.update({Band.name: "Pythonistas 2"})
            .where(Band.name == "Pythonistas")
            .returning(Band.name.as_alias("band name"))
            .run_sync()
        )

        self.assertEqual(response, [{"band name": "Pythonistas 2"}])


###############################################################################
# Test operators


class MyTable(Table):
    integer = Integer(null=True)
    timestamp = Timestamp(null=True)
    timestamptz = Timestamptz(null=True)
    date = Date(null=True)
    interval = Interval(null=True)
    varchar = Varchar(null=True)
    text = Text(null=True)


INITIAL_DATETIME = datetime.datetime(
    year=2022, month=1, day=1, hour=21, minute=0
)
INITIAL_INTERVAL = datetime.timedelta(days=1, hours=1, minutes=1)

DATETIME_DELTA = datetime.timedelta(
    days=1, hours=1, minutes=1, seconds=30, microseconds=1000
)
DATE_DELTA = datetime.timedelta(days=1)


@dataclasses.dataclass
class OperatorTestCase:
    description: str
    column: Column
    initial: t.Any
    querystring: QueryString
    expected: t.Any


TEST_CASES = [
    # Text
    OperatorTestCase(
        description="Add Text",
        column=MyTable.text,
        initial="Pythonistas",
        querystring=MyTable.text + "!!!",
        expected="Pythonistas!!!",
    ),
    OperatorTestCase(
        description="Add Text columns",
        column=MyTable.text,
        initial="Pythonistas",
        querystring=MyTable.text + MyTable.text,
        expected="PythonistasPythonistas",
    ),
    OperatorTestCase(
        description="Reverse add Text",
        column=MyTable.text,
        initial="Pythonistas",
        querystring="!!!" + MyTable.text,
        expected="!!!Pythonistas",
    ),
    OperatorTestCase(
        description="Text is null",
        column=MyTable.text,
        initial=None,
        querystring=MyTable.text + "!!!",
        expected=None,
    ),
    OperatorTestCase(
        description="Reverse Text is null",
        column=MyTable.text,
        initial=None,
        querystring="!!!" + MyTable.text,
        expected=None,
    ),
    # Varchar
    OperatorTestCase(
        description="Add Varchar",
        column=MyTable.varchar,
        initial="Pythonistas",
        querystring=MyTable.varchar + "!!!",
        expected="Pythonistas!!!",
    ),
    OperatorTestCase(
        description="Add Varchar columns",
        column=MyTable.varchar,
        initial="Pythonistas",
        querystring=MyTable.varchar + MyTable.varchar,
        expected="PythonistasPythonistas",
    ),
    OperatorTestCase(
        description="Reverse add Varchar",
        column=MyTable.varchar,
        initial="Pythonistas",
        querystring="!!!" + MyTable.varchar,
        expected="!!!Pythonistas",
    ),
    OperatorTestCase(
        description="Varchar is null",
        column=MyTable.varchar,
        initial=None,
        querystring=MyTable.varchar + "!!!",
        expected=None,
    ),
    OperatorTestCase(
        description="Reverse Varchar is null",
        column=MyTable.varchar,
        initial=None,
        querystring="!!!" + MyTable.varchar,
        expected=None,
    ),
    # Integer
    OperatorTestCase(
        description="Add Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=MyTable.integer + 10,
        expected=1010,
    ),
    OperatorTestCase(
        description="Reverse add Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=10 + MyTable.integer,
        expected=1010,
    ),
    OperatorTestCase(
        description="Add Integer colums together",
        column=MyTable.integer,
        initial=1000,
        querystring=MyTable.integer + MyTable.integer,
        expected=2000,
    ),
    OperatorTestCase(
        description="Subtract Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=MyTable.integer - 10,
        expected=990,
    ),
    OperatorTestCase(
        description="Reverse subtract Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=2000 - MyTable.integer,
        expected=1000,
    ),
    OperatorTestCase(
        description="Multiply Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=MyTable.integer * 2,
        expected=2000,
    ),
    OperatorTestCase(
        description="Reverse multiply Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=2 * MyTable.integer,
        expected=2000,
    ),
    OperatorTestCase(
        description="Divide Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=MyTable.integer / 10,
        expected=100,
    ),
    OperatorTestCase(
        description="Reverse divide Integer",
        column=MyTable.integer,
        initial=1000,
        querystring=2000 / MyTable.integer,
        expected=2,
    ),
    OperatorTestCase(
        description="Integer is null",
        column=MyTable.integer,
        initial=None,
        querystring=MyTable.integer + 1,
        expected=None,
    ),
    OperatorTestCase(
        description="Reverse Integer is null",
        column=MyTable.integer,
        initial=None,
        querystring=1 + MyTable.integer,
        expected=None,
    ),
    # Timestamp
    OperatorTestCase(
        description="Add Timestamp",
        column=MyTable.timestamp,
        initial=INITIAL_DATETIME,
        querystring=MyTable.timestamp + DATETIME_DELTA,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=1000,
        ),
    ),
    OperatorTestCase(
        description="Reverse add Timestamp",
        column=MyTable.timestamp,
        initial=INITIAL_DATETIME,
        querystring=DATETIME_DELTA + MyTable.timestamp,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=1000,
        ),
    ),
    OperatorTestCase(
        description="Subtract Timestamp",
        column=MyTable.timestamp,
        initial=INITIAL_DATETIME,
        querystring=MyTable.timestamp - DATETIME_DELTA,
        expected=datetime.datetime(
            year=2021,
            month=12,
            day=31,
            hour=19,
            minute=58,
            second=29,
            microsecond=999000,
        ),
    ),
    OperatorTestCase(
        description="Timestamp is null",
        column=MyTable.timestamp,
        initial=None,
        querystring=MyTable.timestamp + DATETIME_DELTA,
        expected=None,
    ),
    # Timestamptz
    OperatorTestCase(
        description="Add Timestamptz",
        column=MyTable.timestamptz,
        initial=INITIAL_DATETIME,
        querystring=MyTable.timestamptz + DATETIME_DELTA,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=1000,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    OperatorTestCase(
        description="Reverse add Timestamptz",
        column=MyTable.timestamptz,
        initial=INITIAL_DATETIME,
        querystring=DATETIME_DELTA + MyTable.timestamptz,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=1000,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    OperatorTestCase(
        description="Subtract Timestamptz",
        column=MyTable.timestamptz,
        initial=INITIAL_DATETIME,
        querystring=MyTable.timestamptz - DATETIME_DELTA,
        expected=datetime.datetime(
            year=2021,
            month=12,
            day=31,
            hour=19,
            minute=58,
            second=29,
            microsecond=999000,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    OperatorTestCase(
        description="Timestamptz is null",
        column=MyTable.timestamptz,
        initial=None,
        querystring=MyTable.timestamptz + DATETIME_DELTA,
        expected=None,
    ),
    # Date
    OperatorTestCase(
        description="Add Date",
        column=MyTable.date,
        initial=INITIAL_DATETIME,
        querystring=MyTable.date + DATE_DELTA,
        expected=datetime.date(year=2022, month=1, day=2),
    ),
    OperatorTestCase(
        description="Reverse add Date",
        column=MyTable.date,
        initial=INITIAL_DATETIME,
        querystring=DATE_DELTA + MyTable.date,
        expected=datetime.date(year=2022, month=1, day=2),
    ),
    OperatorTestCase(
        description="Subtract Date",
        column=MyTable.date,
        initial=INITIAL_DATETIME,
        querystring=MyTable.date - DATE_DELTA,
        expected=datetime.date(year=2021, month=12, day=31),
    ),
    OperatorTestCase(
        description="Date is null",
        column=MyTable.date,
        initial=None,
        querystring=MyTable.date + DATE_DELTA,
        expected=None,
    ),
    # Interval
    OperatorTestCase(
        description="Add Interval",
        column=MyTable.interval,
        initial=INITIAL_INTERVAL,
        querystring=MyTable.interval + DATETIME_DELTA,
        expected=datetime.timedelta(days=2, seconds=7350, microseconds=1000),
    ),
    OperatorTestCase(
        description="Reverse add Interval",
        column=MyTable.interval,
        initial=INITIAL_INTERVAL,
        querystring=DATETIME_DELTA + MyTable.interval,
        expected=datetime.timedelta(days=2, seconds=7350, microseconds=1000),
    ),
    OperatorTestCase(
        description="Subtract Interval",
        column=MyTable.interval,
        initial=INITIAL_INTERVAL,
        querystring=MyTable.interval - DATETIME_DELTA,
        expected=datetime.timedelta(
            days=-1, seconds=86369, microseconds=999000
        ),
    ),
    OperatorTestCase(
        description="Interval is null",
        column=MyTable.interval,
        initial=None,
        querystring=MyTable.interval + DATETIME_DELTA,
        expected=None,
    ),
]


class TestOperators(TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()

    @engines_skip("cockroach")
    def test_operators(self):
        for test_case in TEST_CASES:
            print(test_case.description)

            # Create the initial data in the database.
            instance = MyTable()
            setattr(instance, test_case.column._meta.name, test_case.initial)
            instance.save().run_sync()

            # Apply the update.
            MyTable.update(
                {test_case.column: test_case.querystring}, force=True
            ).run_sync()

            # Make sure the value returned from the database is correct.
            new_value = getattr(
                MyTable.objects().first().run_sync(),
                test_case.column._meta.name,
            )

            self.assertEqual(
                new_value, test_case.expected, msg=test_case.description
            )

            # Clean up
            MyTable.delete(force=True).run_sync()

    @sqlite_only
    def test_edge_cases(self):
        """
        Some usecases aren't supported by SQLite, and should raise a
        ``ValueError``.
        """
        with self.assertRaises(ValueError):
            # An error should be raised because we can't save at this level
            # of resolution - 1 millisecond is the minimum.
            MyTable.timestamp + datetime.timedelta(microseconds=1)


###############################################################################
# Test auto_update


class AutoUpdateTable(Table, tablename="my_table"):
    name = Varchar()
    modified_on = Timestamp(
        auto_update=datetime.datetime.now, null=True, default=None
    )


class TestAutoUpdate(TestCase):
    def setUp(self):
        AutoUpdateTable.create_table().run_sync()

    def tearDown(self):
        AutoUpdateTable.alter().drop_table().run_sync()

    def test_save(self):
        """
        Make sure the ``save`` method uses ``auto_update`` columns correctly.
        """
        row = AutoUpdateTable(name="test")

        # Saving for the first time is an INSERT, so `auto_update` shouldn't
        # be triggered.
        row.save().run_sync()
        self.assertIsNone(row.modified_on)

        # A subsequent save is an UPDATE, so `auto_update` should be triggered.
        row.name = "test 2"
        row.save().run_sync()
        self.assertIsInstance(row.modified_on, datetime.datetime)

        # If we save it again, `auto_update` should be applied again.
        existing_modified_on = row.modified_on
        row.name = "test 3"
        row.save().run_sync()
        self.assertIsInstance(row.modified_on, datetime.datetime)
        self.assertGreater(row.modified_on, existing_modified_on)

    def test_update(self):
        """
        Make sure the update method uses ``auto_update`` columns correctly.
        """
        # Insert a row for us to update
        AutoUpdateTable.insert(AutoUpdateTable(name="test")).run_sync()

        self.assertDictEqual(
            AutoUpdateTable.select(
                AutoUpdateTable.name, AutoUpdateTable.modified_on
            )
            .first()
            .run_sync(),
            {"name": "test", "modified_on": None},
        )

        # Update the row
        AutoUpdateTable.update(
            {AutoUpdateTable.name: "test 2"}, force=True
        ).run_sync()

        # Retrieve the row
        updated_row = (
            AutoUpdateTable.select(
                AutoUpdateTable.name, AutoUpdateTable.modified_on
            )
            .first()
            .run_sync()
        )
        self.assertIsInstance(updated_row["modified_on"], datetime.datetime)
        self.assertEqual(updated_row["name"], "test 2")
