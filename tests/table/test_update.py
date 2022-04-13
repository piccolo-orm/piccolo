import dataclasses
import datetime
import typing as t
from unittest import TestCase

from piccolo.columns.base import Column
from piccolo.columns.column_types import Date, Interval, Timestamp, Timestamptz
from piccolo.querystring import QueryString
from piccolo.table import Table
from tests.base import DBTestCase, postgres_only
from tests.example_apps.music.tables import Band, Poster


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


class TestIntUpdateOperators(DBTestCase):
    def test_add(self):
        self.insert_row()

        Band.update(
            {Band.popularity: Band.popularity + 10}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1010)

    def test_add_column(self):
        self.insert_row()

        Band.update(
            {Band.popularity: Band.popularity + Band.popularity}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 2000)

    def test_radd(self):
        self.insert_row()

        Band.update(
            {Band.popularity: 10 + Band.popularity}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1010)

    def test_sub(self):
        self.insert_row()

        Band.update(
            {Band.popularity: Band.popularity - 10}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 990)

    def test_rsub(self):
        self.insert_row()

        Band.update(
            {Band.popularity: 1100 - Band.popularity}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 100)

    def test_mul(self):
        self.insert_row()

        Band.update(
            {Band.popularity: Band.popularity * 2}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 2000)

    def test_rmul(self):
        self.insert_row()

        Band.update(
            {Band.popularity: 2 * Band.popularity}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 2000)

    def test_div(self):
        self.insert_row()

        Band.update(
            {Band.popularity: Band.popularity / 10}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 100)

    def test_rdiv(self):
        self.insert_row()

        Band.update(
            {Band.popularity: 1000 / Band.popularity}, force=True
        ).run_sync()

        response = Band.select(Band.popularity).first().run_sync()

        self.assertEqual(response["popularity"], 1)


class TestVarcharUpdateOperators(DBTestCase):
    def test_add(self):
        self.insert_row()

        Band.update({Band.name: Band.name + "!!!"}, force=True).run_sync()

        response = Band.select(Band.name).first().run_sync()

        self.assertEqual(response["name"], "Pythonistas!!!")

    def test_add_column(self):
        self.insert_row()

        Band.update({Band.name: Band.name + Band.name}, force=True).run_sync()

        response = Band.select(Band.name).first().run_sync()

        self.assertEqual(response["name"], "PythonistasPythonistas")

    def test_radd(self):
        self.insert_row()

        Band.update({Band.name: "!!!" + Band.name}, force=True).run_sync()

        response = Band.select(Band.name).first().run_sync()

        self.assertEqual(response["name"], "!!!Pythonistas")


class TestTextUpdateOperators(DBTestCase):
    def setUp(self):
        super().setUp()
        Poster(content="Join us for this amazing show").save().run_sync()

    def test_add(self):
        Poster.update(
            {Poster.content: Poster.content + "!!!"}, force=True
        ).run_sync()

        response = Poster.select(Poster.content).first().run_sync()

        self.assertEqual(
            response["content"], "Join us for this amazing show!!!"
        )

    def test_add_column(self):
        self.insert_row()

        Poster.update(
            {Poster.content: Poster.content + Poster.content}, force=True
        ).run_sync()

        response = Poster.select(Poster.content).first().run_sync()

        self.assertEqual(
            response["content"],
            "Join us for this amazing show" * 2,
        )

    def test_radd(self):
        self.insert_row()

        Poster.update(
            {Poster.content: "!!!" + Poster.content}, force=True
        ).run_sync()

        response = Poster.select(Poster.content).first().run_sync()

        self.assertEqual(
            response["content"], "!!!Join us for this amazing show"
        )


###############################################################################


class Concert(Table):
    timestamp = Timestamp()
    timestamptz = Timestamptz()
    date = Date()
    interval = Interval()


INITIAL_DATETIME = datetime.datetime(
    year=2022, month=1, day=1, hour=21, minute=0
)
INITIAL_INTERVAL = datetime.timedelta(days=1, hours=1, minutes=1)

DELTA = datetime.timedelta(
    days=1, hours=1, minutes=1, seconds=30, microseconds=500
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
    # Timestamp
    OperatorTestCase(
        description="Add Timestamp",
        column=Concert.timestamp,
        initial=INITIAL_DATETIME,
        querystring=Concert.timestamp + DELTA,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=500,
        ),
    ),
    OperatorTestCase(
        description="Reverse add Timestamp",
        column=Concert.timestamp,
        initial=INITIAL_DATETIME,
        querystring=DELTA + Concert.timestamp,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=500,
        ),
    ),
    OperatorTestCase(
        description="Subtract Timestamp",
        column=Concert.timestamp,
        initial=INITIAL_DATETIME,
        querystring=Concert.timestamp - DELTA,
        expected=datetime.datetime(
            year=2021,
            month=12,
            day=31,
            hour=19,
            minute=58,
            second=29,
            microsecond=999500,
        ),
    ),
    # Timestamptz
    OperatorTestCase(
        description="Add Timestamptz",
        column=Concert.timestamptz,
        initial=INITIAL_DATETIME,
        querystring=Concert.timestamptz + DELTA,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=500,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    OperatorTestCase(
        description="Reverse add Timestamptz",
        column=Concert.timestamptz,
        initial=INITIAL_DATETIME,
        querystring=DELTA + Concert.timestamptz,
        expected=datetime.datetime(
            year=2022,
            month=1,
            day=2,
            hour=22,
            minute=1,
            second=30,
            microsecond=500,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    OperatorTestCase(
        description="Subtract Timestamptz",
        column=Concert.timestamptz,
        initial=INITIAL_DATETIME,
        querystring=Concert.timestamptz - DELTA,
        expected=datetime.datetime(
            year=2021,
            month=12,
            day=31,
            hour=19,
            minute=58,
            second=29,
            microsecond=999500,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    # Date
    OperatorTestCase(
        description="Add Date",
        column=Concert.date,
        initial=INITIAL_DATETIME,
        querystring=Concert.date + DATE_DELTA,
        expected=datetime.date(year=2022, month=1, day=2),
    ),
    OperatorTestCase(
        description="Reverse add Date",
        column=Concert.date,
        initial=INITIAL_DATETIME,
        querystring=DATE_DELTA + Concert.date,
        expected=datetime.date(year=2022, month=1, day=2),
    ),
    OperatorTestCase(
        description="Subtract Date",
        column=Concert.date,
        initial=INITIAL_DATETIME,
        querystring=Concert.date - DATE_DELTA,
        expected=datetime.date(year=2021, month=12, day=31),
    ),
    # Interval
    OperatorTestCase(
        description="Add Interval",
        column=Concert.interval,
        initial=INITIAL_INTERVAL,
        querystring=Concert.interval + DELTA,
        expected=datetime.timedelta(days=2, seconds=7350, microseconds=500),
    ),
    OperatorTestCase(
        description="Reverse add Interval",
        column=Concert.interval,
        initial=INITIAL_INTERVAL,
        querystring=DELTA + Concert.interval,
        expected=datetime.timedelta(days=2, seconds=7350, microseconds=500),
    ),
    OperatorTestCase(
        description="Subtract Interval",
        column=Concert.interval,
        initial=INITIAL_INTERVAL,
        querystring=Concert.interval - DELTA,
        expected=datetime.timedelta(
            days=-1, seconds=86369, microseconds=999500
        ),
    ),
]


# TODO - add SQLite support
@postgres_only
class TestOperators(TestCase):
    def setUp(self):
        Concert.create_table().run_sync()

    def tearDown(self):
        Concert.alter().drop_table().run_sync()

    def test_operators(self):
        for test_case in TEST_CASES:
            # Create the initial data in the database.
            concert = Concert()
            setattr(concert, test_case.column._meta.name, test_case.initial)
            concert.save().run_sync()

            # Apply the update.
            Concert.update(
                {test_case.column: test_case.querystring}, force=True
            ).run_sync()

            # Make sure the value returned from the database is correct.
            new_value = getattr(
                Concert.objects().first().run_sync(),
                test_case.column._meta.name,
            )
            self.assertEqual(
                new_value, test_case.expected, msg=test_case.description
            )

            # Clean up
            Concert.delete(force=True).run_sync()
