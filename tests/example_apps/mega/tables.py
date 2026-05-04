"""
This is a useful table when we want to test all possible column types.
"""

from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    BigInt,
    Boolean,
    Bytea,
    Date,
    DoublePrecision,
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
from piccolo.engine.finder import engine_finder
from piccolo.table import Table

engine = engine_finder()


class SmallTable(Table):
    varchar_col = Varchar()


if engine.engine_type != "cockroach":  # type: ignore

    class MegaTable(Table):  # type: ignore
        """
        A table containing all of the column types, different column kwargs.
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
        numeric_col = Numeric(digits=(5, 2))
        real_col = Real()
        double_precision_col = DoublePrecision()
        smallint_col = SmallInt()
        text_col = Text()
        timestamp_col = Timestamp()
        timestamptz_col = Timestamptz()
        uuid_col = UUID()
        varchar_col = Varchar()

        unique_col = Varchar(unique=True)
        null_col = Varchar(null=True)
        not_null_col = Varchar(null=False)

else:

    class MegaTable(Table):  # type: ignore
        """
        Special version for Cockroach.
        A table containing all of the column types, different column kwargs.
        """

        bigint_col = BigInt()
        boolean_col = Boolean()
        bytea_col = Bytea()
        date_col = Date()
        foreignkey_col = ForeignKey(SmallTable)
        integer_col = BigInt()
        interval_col = Interval()
        json_col = JSONB()
        jsonb_col = JSONB()
        numeric_col = Numeric(digits=(5, 2))
        real_col = Real()
        double_precision_col = DoublePrecision()
        smallint_col = SmallInt()
        text_col = Text()
        timestamp_col = Timestamp()
        timestamptz_col = Timestamptz()
        uuid_col = UUID()
        varchar_col = Varchar()

        unique_col = Varchar(unique=True)
        null_col = Varchar(null=True)
        not_null_col = Varchar(null=False)
