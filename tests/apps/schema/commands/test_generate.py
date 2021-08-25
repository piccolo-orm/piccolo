from __future__ import annotations

import typing as t
from unittest import TestCase

from piccolo.apps.schema.commands.generate import (
    OutputSchema,
    get_output_schema,
)
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    BigInt,
    Boolean,
    Bytea,
    Date,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    Real,
    SmallInt,
    Text,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.table import Table
from piccolo.utils.sync import run_sync
from tests.base import postgres_only


class SmallTable(Table):
    varchar_col = Varchar()


class MegaTable(Table):
    """
    A table containing all of the column types, and different column kwargs.
    """

    bigint_col = BigInt()
    boolean_col = Boolean()
    bytea_col = Bytea()
    date_col = Date()
    foreignkey_col = ForeignKey(SmallTable)
    integer_col = Integer()
    interval_col = Interval()
    json_col = JSON()
    jsonb_col = JSONB()
    numeric_col = Numeric()
    real_col = Real()
    smallint_col = SmallInt()
    text_col = Text()
    timestamp_col = Timestamp()
    timestamptz_col = Timestamptz()
    uuid_col = UUID()
    varchar_col = Varchar()

    unique_col = Varchar(unique=True)
    null_col = Varchar(null=True)
    not_null_col = Varchar(null=False)


@postgres_only
class TestGenerate(TestCase):
    def setUp(self):
        for table_class in (SmallTable, MegaTable):
            table_class.create_table().run_sync()

    def tearDown(self):
        for table_class in (MegaTable, SmallTable):
            table_class.alter().drop_table().run_sync()

    def _compare_table_columns(
        self, table_1: t.Type[Table], table_2: t.Type[Table]
    ):
        """
        Make sure that for each column in table_1, there is a corresponding
        column in table_2 of the same type.
        """
        column_names = [
            column._meta.name for column in table_1._meta.non_default_columns
        ]
        for column_name in column_names:
            col_1 = table_1._meta.get_column_by_name(column_name)
            col_2 = table_2._meta.get_column_by_name(column_name)

            # Make sure they're the same type
            self.assertEqual(type(col_1), type(col_2))

            # Make sure they're both nullable or not
            self.assertEqual(col_1._meta.null, col_2._meta.null)

            # Make sure the max length is the same
            if isinstance(col_1, Varchar) and isinstance(col_2, Varchar):
                self.assertEqual(col_1.length, col_2.length)

            # Make sure the unique constraint is the same
            self.assertEqual(col_1._meta.unique, col_2._meta.unique)

    def test_get_output_schema(self):
        """
        Make sure that the a Piccolo schema can be generated from the database.
        """
        output_schema: OutputSchema = run_sync(get_output_schema())

        self.assertTrue(len(output_schema.warnings) == 0)
        self.assertTrue(len(output_schema.tables) == 2)
        self.assertTrue(len(output_schema.imports) > 0)

        MegaTable_ = output_schema.get_table_with_name("MegaTable")
        self._compare_table_columns(MegaTable, MegaTable_)

        SmallTable_ = output_schema.get_table_with_name("SmallTable")
        self._compare_table_columns(SmallTable, SmallTable_)
