import asyncio
import datetime
import decimal
import uuid
from unittest import TestCase

from tests.base import engines_skip

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

from .base import M2MBase

engine = engine_finder()


class TestM2M(M2MBase, TestCase):
    def setUp(self):
        return self._setUp(schema=None)


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
        customer = Customer.objects().get(Customer.name == "Bob").run_sync()
        assert customer is not None
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
                customer = await Customer.objects().get(Customer.name == "Bob")
                assert customer is not None
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
        customer = Customer.objects().get(Customer.name == "Bob").run_sync()
        assert customer is not None

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

            if isinstance(column, UUID):
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

            if isinstance(column, UUID):
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
