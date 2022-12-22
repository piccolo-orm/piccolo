import asyncio
import datetime
import decimal
import uuid
from unittest import TestCase

from tests.base import engine_is, engines_skip

try:
    from asyncpg.pgproto.pgproto import UUID as asyncpgUUID
except ImportError:
    # In case someone is running the tests for SQLite and doesn't have asyncpg
    # installed.
    from uuid import UUID as asyncpgUUID

from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    Array,
    BigInt,
    Boolean,
    Bytea,
    Date,
    DoublePrecision,
    ForeignKey,
    Integer,
    Interval,
    LazyTableReference,
    Numeric,
    Real,
    SmallInt,
    Text,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.columns.m2m import M2M
from piccolo.engine.finder import engine_finder
from piccolo.table import Table, create_db_tables_sync, drop_db_tables_sync

engine = engine_finder()


class Band(Table):
    name = Varchar()
    genres = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class Genre(Table):
    name = Varchar()
    bands = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class GenreToBand(Table):
    band = ForeignKey(Band)
    genre = ForeignKey(Genre)
    reason = Text(help_text="For testing additional columns on join tables.")


SIMPLE_SCHEMA = [Band, Genre, GenreToBand]


class TestM2M(TestCase):
    def setUp(self):
        create_db_tables_sync(*SIMPLE_SCHEMA, if_not_exists=True)

        if engine_is("cockroach"):
            bands = (
                Band.insert(
                    Band(name="Pythonistas"),
                    Band(name="Rustaceans"),
                    Band(name="C-Sharps"),
                )
                .returning(Band.id)
                .run_sync()
            )

            genres = (
                Genre.insert(
                    Genre(name="Rock"),
                    Genre(name="Folk"),
                    Genre(name="Classical"),
                )
                .returning(Genre.id)
                .run_sync()
            )

            GenreToBand.insert(
                GenreToBand(band=bands[0]["id"], genre=genres[0]["id"]),
                GenreToBand(band=bands[0]["id"], genre=genres[1]["id"]),
                GenreToBand(band=bands[1]["id"], genre=genres[1]["id"]),
                GenreToBand(band=bands[2]["id"], genre=genres[0]["id"]),
                GenreToBand(band=bands[2]["id"], genre=genres[2]["id"]),
            ).run_sync()
        else:
            Band.insert(
                Band(name="Pythonistas"),
                Band(name="Rustaceans"),
                Band(name="C-Sharps"),
            ).run_sync()

            Genre.insert(
                Genre(name="Rock"),
                Genre(name="Folk"),
                Genre(name="Classical"),
            ).run_sync()

            GenreToBand.insert(
                GenreToBand(band=1, genre=1),
                GenreToBand(band=1, genre=2),
                GenreToBand(band=2, genre=2),
                GenreToBand(band=3, genre=1),
                GenreToBand(band=3, genre=3),
            ).run_sync()

    def tearDown(self):
        drop_db_tables_sync(*SIMPLE_SCHEMA)

    @engines_skip("cockroach")
    def test_select_name(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        response = Band.select(
            Band.name, Band.genres(Genre.name, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": ["Rock", "Folk"]},
                {"name": "Rustaceans", "genres": ["Folk"]},
                {"name": "C-Sharps", "genres": ["Rock", "Classical"]},
            ],
        )

        # Now try it in reverse.
        response = Genre.select(
            Genre.name, Genre.bands(Band.name, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Rock", "bands": ["Pythonistas", "C-Sharps"]},
                {"name": "Folk", "bands": ["Pythonistas", "Rustaceans"]},
                {"name": "Classical", "bands": ["C-Sharps"]},
            ],
        )

    @engines_skip("cockroach")
    def test_no_related(self):
        """
        Make sure it still works correctly if there are no related values.
        """
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        GenreToBand.delete(force=True).run_sync()

        # Try it with a list response
        response = Band.select(
            Band.name, Band.genres(Genre.name, as_list=True)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": []},
                {"name": "Rustaceans", "genres": []},
                {"name": "C-Sharps", "genres": []},
            ],
        )

        # Also try it with a nested response
        response = Band.select(
            Band.name, Band.genres(Genre.id, Genre.name)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": []},
                {"name": "Rustaceans", "genres": []},
                {"name": "C-Sharps", "genres": []},
            ],
        )

    @engines_skip("cockroach")
    def test_select_multiple(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        response = Band.select(
            Band.name, Band.genres(Genre.id, Genre.name)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "genres": [
                        {"id": 1, "name": "Rock"},
                        {"id": 2, "name": "Folk"},
                    ],
                },
                {"name": "Rustaceans", "genres": [{"id": 2, "name": "Folk"}]},
                {
                    "name": "C-Sharps",
                    "genres": [
                        {"id": 1, "name": "Rock"},
                        {"id": 3, "name": "Classical"},
                    ],
                },
            ],
        )

        # Now try it in reverse.
        response = Genre.select(
            Genre.name, Genre.bands(Band.id, Band.name)
        ).run_sync()

        self.assertEqual(
            response,
            [
                {
                    "name": "Rock",
                    "bands": [
                        {"id": 1, "name": "Pythonistas"},
                        {"id": 3, "name": "C-Sharps"},
                    ],
                },
                {
                    "name": "Folk",
                    "bands": [
                        {"id": 1, "name": "Pythonistas"},
                        {"id": 2, "name": "Rustaceans"},
                    ],
                },
                {
                    "name": "Classical",
                    "bands": [{"id": 3, "name": "C-Sharps"}],
                },
            ],
        )

    @engines_skip("cockroach")
    def test_select_id(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        response = Band.select(
            Band.name, Band.genres(Genre.id, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Pythonistas", "genres": [1, 2]},
                {"name": "Rustaceans", "genres": [2]},
                {"name": "C-Sharps", "genres": [1, 3]},
            ],
        )

        # Now try it in reverse.
        response = Genre.select(
            Genre.name, Genre.bands(Band.id, as_list=True)
        ).run_sync()
        self.assertEqual(
            response,
            [
                {"name": "Rock", "bands": [1, 3]},
                {"name": "Folk", "bands": [1, 2]},
                {"name": "Classical", "bands": [3]},
            ],
        )

    @engines_skip("cockroach")
    def test_select_all_columns(self):
        """
        Make sure ``all_columns`` can be passed in as an argument. ``M2M``
        should flatten the arguments. Reported here:

        https://github.com/piccolo-orm/piccolo/issues/728

        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg

        """  # noqa: E501
        response = Band.select(
            Band.name, Band.genres(Genre.all_columns(exclude=(Genre.id,)))
        ).run_sync()
        self.assertEqual(
            response,
            [
                {
                    "name": "Pythonistas",
                    "genres": [
                        {"name": "Rock"},
                        {"name": "Folk"},
                    ],
                },
                {"name": "Rustaceans", "genres": [{"name": "Folk"}]},
                {
                    "name": "C-Sharps",
                    "genres": [
                        {"name": "Rock"},
                        {"name": "Classical"},
                    ],
                },
            ],
        )

    def test_add_m2m(self):
        """
        Make sure we can add items to the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(Genre(name="Punk Rock"), m2m=Band.genres).run_sync()

        self.assertTrue(
            Genre.exists().where(Genre.name == "Punk Rock").run_sync()
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Punk Rock",
            )
            .run_sync(),
            1,
        )

    def test_extra_columns_str(self):
        """
        Make sure the ``extra_column_values`` parameter for ``add_m2m`` works
        correctly when the dictionary keys are strings.
        """
        reason = "Their second album was very punk rock."

        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(
            Genre(name="Punk Rock"),
            m2m=Band.genres,
            extra_column_values={
                "reason": "Their second album was very punk rock."
            },
        ).run_sync()

        genre_to_band = (
            GenreToBand.objects()
            .get(
                (GenreToBand.band.name == "Pythonistas")
                & (GenreToBand.genre.name == "Punk Rock")
            )
            .run_sync()
        )

        self.assertEqual(genre_to_band.reason, reason)

    def test_extra_columns_class(self):
        """
        Make sure the ``extra_column_values`` parameter for ``add_m2m`` works
        correctly when the dictionary keys are ``Column`` classes.
        """
        reason = "Their second album was very punk rock."

        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()
        band.add_m2m(
            Genre(name="Punk Rock"),
            m2m=Band.genres,
            extra_column_values={
                GenreToBand.reason: "Their second album was very punk rock."
            },
        ).run_sync()

        genre_to_band = (
            GenreToBand.objects()
            .get(
                (GenreToBand.band.name == "Pythonistas")
                & (GenreToBand.genre.name == "Punk Rock")
            )
            .run_sync()
        )

        self.assertEqual(genre_to_band.reason, reason)

    def test_add_m2m_existing(self):
        """
        Make sure we can add an existing element to the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genre: Genre = (
            Genre.objects().get(Genre.name == "Classical").run_sync()
        )

        band.add_m2m(genre, m2m=Band.genres).run_sync()

        # We shouldn't have created a duplicate genre in the database.
        self.assertEqual(
            Genre.count().where(Genre.name == "Classical").run_sync(), 1
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Classical",
            )
            .run_sync(),
            1,
        )

    def test_get_m2m(self):
        """
        Make sure we can get related items via the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genres = band.get_m2m(Band.genres).run_sync()

        self.assertTrue(all(isinstance(i, Table) for i in genres))

        self.assertEqual([i.name for i in genres], ["Rock", "Folk"])

    def test_remove_m2m(self):
        """
        Make sure we can remove related items via the joining table.
        """
        band: Band = Band.objects().get(Band.name == "Pythonistas").run_sync()

        genre = Genre.objects().get(Genre.name == "Rock").run_sync()

        band.remove_m2m(genre, m2m=Band.genres).run_sync()

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Rock",
            )
            .run_sync(),
            0,
        )

        # Make sure the others weren't removed:
        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "Pythonistas",
                GenreToBand.genre.name == "Folk",
            )
            .run_sync(),
            1,
        )

        self.assertEqual(
            GenreToBand.count()
            .where(
                GenreToBand.band.name == "C-Sharps",
                GenreToBand.genre.name == "Rock",
            )
            .run_sync(),
            1,
        )


###############################################################################

# A schema using custom primary keys


class Customer(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    concerts = M2M(
        LazyTableReference("CustomerToConcert", module_path=__name__)
    )


class Concert(Table):
    uuid = UUID(primary_key=True)
    name = Varchar()
    customers = M2M(
        LazyTableReference("CustomerToConcert", module_path=__name__)
    )


class CustomerToConcert(Table):
    customer = ForeignKey(Customer)
    concert = ForeignKey(Concert)


CUSTOM_PK_SCHEMA = [Customer, Concert, CustomerToConcert]


class TestM2MCustomPrimaryKey(TestCase):
    """
    Make sure the M2M functionality works correctly when the tables have custom
    primary key columns.
    """

    def setUp(self):
        create_db_tables_sync(*CUSTOM_PK_SCHEMA, if_not_exists=True)

        bob = Customer.objects().create(name="Bob").run_sync()
        sally = Customer.objects().create(name="Sally").run_sync()
        fred = Customer.objects().create(name="Fred").run_sync()

        rockfest = Concert.objects().create(name="Rockfest").run_sync()
        folkfest = Concert.objects().create(name="Folkfest").run_sync()
        classicfest = Concert.objects().create(name="Classicfest").run_sync()

        CustomerToConcert.insert(
            CustomerToConcert(customer=bob, concert=rockfest),
            CustomerToConcert(customer=bob, concert=classicfest),
            CustomerToConcert(customer=sally, concert=rockfest),
            CustomerToConcert(customer=sally, concert=folkfest),
            CustomerToConcert(customer=fred, concert=classicfest),
        ).run_sync()

    def tearDown(self):
        drop_db_tables_sync(*CUSTOM_PK_SCHEMA)

    @engines_skip("cockroach")
    def test_select(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        response = Customer.select(
            Customer.name, Customer.concerts(Concert.name, as_list=True)
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {"name": "Bob", "concerts": ["Rockfest", "Classicfest"]},
                {"name": "Sally", "concerts": ["Rockfest", "Folkfest"]},
                {"name": "Fred", "concerts": ["Classicfest"]},
            ],
        )

        # Now try it in reverse.
        response = Concert.select(
            Concert.name, Concert.customers(Customer.name, as_list=True)
        ).run_sync()

        self.assertListEqual(
            response,
            [
                {"name": "Rockfest", "customers": ["Bob", "Sally"]},
                {"name": "Folkfest", "customers": ["Sally"]},
                {"name": "Classicfest", "customers": ["Bob", "Fred"]},
            ],
        )

    def test_add_m2m(self):
        """
        Make sure we can add items to the joining table.
        """
        customer: Customer = (
            Customer.objects().get(Customer.name == "Bob").run_sync()
        )
        customer.add_m2m(
            Concert(name="Jazzfest"), m2m=Customer.concerts
        ).run_sync()

        self.assertTrue(
            Concert.exists().where(Concert.name == "Jazzfest").run_sync()
        )

        self.assertEqual(
            CustomerToConcert.count()
            .where(
                CustomerToConcert.customer.name == "Bob",
                CustomerToConcert.concert.name == "Jazzfest",
            )
            .run_sync(),
            1,
        )

    def test_add_m2m_within_transaction(self):
        """
        Make sure we can add items to the joining table, when within an
        existing transaction.

        https://github.com/piccolo-orm/piccolo/issues/674

        """
        engine = Customer._meta.db

        async def add_m2m_in_transaction():
            async with engine.transaction():
                customer: Customer = await Customer.objects().get(
                    Customer.name == "Bob"
                )
                await customer.add_m2m(
                    Concert(name="Jazzfest"), m2m=Customer.concerts
                )

        asyncio.run(add_m2m_in_transaction())

        self.assertTrue(
            Concert.exists().where(Concert.name == "Jazzfest").run_sync()
        )

        self.assertEqual(
            CustomerToConcert.count()
            .where(
                CustomerToConcert.customer.name == "Bob",
                CustomerToConcert.concert.name == "Jazzfest",
            )
            .run_sync(),
            1,
        )

    def test_get_m2m(self):
        """
        Make sure we can get related items via the joining table.
        """
        customer: Customer = (
            Customer.objects().get(Customer.name == "Bob").run_sync()
        )

        concerts = customer.get_m2m(Customer.concerts).run_sync()

        self.assertTrue(all(isinstance(i, Table) for i in concerts))

        self.assertCountEqual(
            [i.name for i in concerts], ["Rockfest", "Classicfest"]
        )


###############################################################################

# Test a very complex schema


class SmallTable(Table):
    varchar_col = Varchar()
    mega_rows = M2M(LazyTableReference("SmallToMega", module_path=__name__))


if engine.engine_type != "cockroach":  # type: ignore

    class MegaTable(Table):  # type: ignore
        """
        A table containing all of the column types and different column kwargs
        """

        array_col = Array(Varchar())
        bigint_col = BigInt()
        boolean_col = Boolean()
        bytea_col = Bytea()
        date_col = Date()
        double_precision_col = DoublePrecision()
        integer_col = Integer()
        interval_col = Interval()
        json_col = JSON()
        jsonb_col = JSONB()
        numeric_col = Numeric(digits=(5, 2))
        real_col = Real()
        smallint_col = SmallInt()
        text_col = Text()
        timestamp_col = Timestamp()
        timestamptz_col = Timestamptz()
        uuid_col = UUID()
        varchar_col = Varchar()

else:

    class MegaTable(Table):  # type: ignore
        """
        Special version for Cockroach.
        A table containing all of the column types and different column kwargs
        """

        array_col = Array(Varchar())
        bigint_col = BigInt()
        boolean_col = Boolean()
        bytea_col = Bytea()
        date_col = Date()
        double_precision_col = DoublePrecision()
        integer_col = BigInt()
        interval_col = Interval()
        json_col = JSONB()
        jsonb_col = JSONB()
        numeric_col = Numeric(digits=(5, 2))
        real_col = Real()
        smallint_col = SmallInt()
        text_col = Text()
        timestamp_col = Timestamp()
        timestamptz_col = Timestamptz()
        uuid_col = UUID()
        varchar_col = Varchar()


class SmallToMega(Table):
    small = ForeignKey(MegaTable)
    mega = ForeignKey(SmallTable)


COMPLEX_SCHEMA = [MegaTable, SmallTable, SmallToMega]


class TestM2MComplexSchema(TestCase):
    """
    By using a very complex schema containing every column type, we can catch
    more edge cases.
    """

    def setUp(self):
        create_db_tables_sync(*COMPLEX_SCHEMA, if_not_exists=True)

        small_table = SmallTable(varchar_col="Test")
        small_table.save().run_sync()

        mega_table = MegaTable(
            array_col=["bob", "sally"],
            bigint_col=1,
            boolean_col=True,
            bytea_col="hello".encode("utf8"),
            date_col=datetime.date(year=2021, month=1, day=1),
            double_precision_col=1.344,
            integer_col=1,
            interval_col=datetime.timedelta(seconds=10),
            json_col={"a": 1},
            jsonb_col={"a": 1},
            numeric_col=decimal.Decimal("1.1"),
            real_col=1.1,
            smallint_col=1,
            text_col="hello",
            timestamp_col=datetime.datetime(year=2021, month=1, day=1),
            timestamptz_col=datetime.datetime(
                year=2021, month=1, day=1, tzinfo=datetime.timezone.utc
            ),
            uuid_col=uuid.UUID("12783854-c012-4c15-8183-8eecb46f2c4e"),
            varchar_col="hello",
        )
        mega_table.save().run_sync()

        SmallToMega(small=small_table, mega=mega_table).save().run_sync()

        self.mega_table = mega_table

    def tearDown(self):
        drop_db_tables_sync(*COMPLEX_SCHEMA)

    @engines_skip("cockroach")
    def test_select_all(self):
        """
        Fetch all of the columns from the related table to make sure they're
        returned correctly.
        """
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        response = SmallTable.select(
            SmallTable.varchar_col, SmallTable.mega_rows(load_json=True)
        ).run_sync()

        self.assertEqual(len(response), 1)
        mega_rows = response[0]["mega_rows"]

        self.assertEqual(len(mega_rows), 1)
        mega_row = mega_rows[0]

        for key, value in mega_row.items():
            # Make sure that every value in the response matches what we saved.
            self.assertAlmostEqual(
                getattr(self.mega_table, key),
                value,
                msg=f"{key} doesn't match",
            )

    @engines_skip("cockroach")
    def test_select_single(self):
        """
        Make sure each column can be selected one at a time.
        """
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/71908 "could not decorrelate subquery" error under asyncpg
        """  # noqa: E501
        for column in MegaTable._meta.columns:
            response = SmallTable.select(
                SmallTable.varchar_col,
                SmallTable.mega_rows(column, load_json=True),
            ).run_sync()

            data = response[0]["mega_rows"][0]
            column_name = column._meta.name

            original_value = getattr(self.mega_table, column_name)
            returned_value = data[column_name]

            if type(column) == UUID:
                self.assertIn(type(returned_value), (uuid.UUID, asyncpgUUID))
            else:
                self.assertEqual(
                    type(original_value),
                    type(returned_value),
                    msg=f"{column_name} type isn't correct",
                )

                self.assertAlmostEqual(
                    original_value,
                    returned_value,
                    msg=f"{column_name} doesn't match",
                )

            # Test it as a list too
            response = SmallTable.select(
                SmallTable.varchar_col,
                SmallTable.mega_rows(column, as_list=True, load_json=True),
            ).run_sync()

            original_value = getattr(self.mega_table, column_name)
            returned_value = response[0]["mega_rows"][0]

            if type(column) == UUID:
                self.assertIn(type(returned_value), (uuid.UUID, asyncpgUUID))
                self.assertEqual(str(original_value), str(returned_value))
            else:
                self.assertEqual(
                    type(original_value),
                    type(returned_value),
                    msg=f"{column_name} type isn't correct",
                )

                self.assertAlmostEqual(
                    original_value,
                    returned_value,
                    msg=f"{column_name} doesn't match",
                )
