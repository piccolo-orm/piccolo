import datetime
import decimal
import uuid
from unittest import TestCase

from piccolo.apps.fixtures.commands.dump import (
    FixtureConfig,
    dump_to_json_string,
)
from piccolo.apps.fixtures.commands.load import load_json_string
from piccolo.utils.sync import run_sync
from tests.example_apps.mega.tables import MegaTable, SmallTable


class TestDumpLoad(TestCase):
    """
    Test the fixture dump and load commands - makes sense to test them
    together.
    """

    maxDiff = None

    def setUp(self):
        for table_class in (SmallTable, MegaTable):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (MegaTable, SmallTable):
            table_class.alter().drop_table().run_sync()

    def insert_row(self):
        small_table = SmallTable(varchar_col="Test")
        small_table.save().run_sync()

        mega_table = MegaTable(
            bigint_col=1,
            boolean_col=True,
            bytea_col="hello".encode("utf8"),
            date_col=datetime.date(year=2021, month=1, day=1),
            foreignkey_col=small_table,
            integer_col=1,
            interval_col=datetime.timedelta(seconds=10),
            json_col={"a": 1},
            jsonb_col={"a": 1},
            numeric_col=decimal.Decimal("1.1"),
            real_col=1.1,
            double_precision_col=1.344,
            smallint_col=1,
            text_col="hello",
            timestamp_col=datetime.datetime(year=2021, month=1, day=1),
            timestamptz_col=datetime.datetime(
                year=2021, month=1, day=1, tzinfo=datetime.timezone.utc
            ),
            uuid_col=uuid.UUID("12783854-c012-4c15-8183-8eecb46f2c4e"),
            varchar_col="hello",
            unique_col="hello",
            null_col=None,
            not_null_col="hello",
        )
        mega_table.save().run_sync()

    def test_dump_load(self):
        """
        Make sure we can dump some rows into a JSON fixture, then load them
        back into the database.
        """
        self.insert_row()

        json_string = run_sync(
            dump_to_json_string(
                fixture_configs=[
                    FixtureConfig(
                        app_name="mega",
                        table_class_names=["SmallTable", "MegaTable"],
                    )
                ]
            )
        )

        # We need to clear the data out now, otherwise when loading the data
        # back in, there will be a constraint errors over clashing primary
        # keys.
        SmallTable.delete(force=True).run_sync()
        MegaTable.delete(force=True).run_sync()

        run_sync(load_json_string(json_string))

        self.assertEqual(
            SmallTable.select().run_sync(),
            [{"id": 1, "varchar_col": "Test"}],
        )

        mega_table_data = MegaTable.select().run_sync()

        # Real numbers don't have perfect precision when coming back from the
        # database, so we need to round them to be able to compare them.
        mega_table_data[0]["real_col"] = round(
            mega_table_data[0]["real_col"], 1
        )

        # Remove white space from the JSON values
        for col_name in ("json_col", "jsonb_col"):
            mega_table_data[0][col_name] = mega_table_data[0][
                col_name
            ].replace(" ", "")

        self.assertTrue(len(mega_table_data) == 1)

        self.assertDictEqual(
            mega_table_data[0],
            {
                "id": 1,
                "bigint_col": 1,
                "boolean_col": True,
                "bytea_col": b"hello",
                "date_col": datetime.date(2021, 1, 1),
                "foreignkey_col": 1,
                "integer_col": 1,
                "interval_col": datetime.timedelta(seconds=10),
                "json_col": '{"a":1}',
                "jsonb_col": '{"a":1}',
                "numeric_col": decimal.Decimal("1.1"),
                "real_col": 1.1,
                "double_precision_col": 1.344,
                "smallint_col": 1,
                "text_col": "hello",
                "timestamp_col": datetime.datetime(2021, 1, 1, 0, 0),
                "timestamptz_col": datetime.datetime(
                    2021, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
                ),
                "uuid_col": uuid.UUID("12783854-c012-4c15-8183-8eecb46f2c4e"),
                "varchar_col": "hello",
                "unique_col": "hello",
                "null_col": None,
                "not_null_col": "hello",
            },
        )
