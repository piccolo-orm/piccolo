from __future__ import annotations

import datetime
import decimal
import os
import random
import shutil
import tempfile
import time
import typing as t
import uuid
from unittest.mock import MagicMock, patch

from piccolo.apps.migrations.commands.forwards import ForwardsMigrationManager
from piccolo.apps.migrations.commands.new import (
    _create_migrations_folder,
    _create_new_migration,
)
from piccolo.apps.migrations.tables import Migration
from piccolo.apps.schema.commands.generate import RowMeta
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    Array,
    BigInt,
    BigSerial,
    Boolean,
    Date,
    Decimal,
    DoublePrecision,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    Real,
    Serial,
    SmallInt,
    Text,
    Time,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.columns.defaults.uuid import UUID4
from piccolo.columns.m2m import M2M
from piccolo.columns.reference import LazyTableReference
from piccolo.conf.apps import AppConfig
from piccolo.table import Table, create_table_class, drop_db_tables_sync
from piccolo.utils.sync import run_sync
from tests.base import DBTestCase, engines_only, engines_skip

if t.TYPE_CHECKING:
    from piccolo.columns.base import Column


def string_default():
    return "hello world"


def integer_default():
    return 1


def uuid_default():
    return uuid.uuid4()


def datetime_default():
    return datetime.datetime.now()


def time_default():
    return datetime.datetime.now().time()


def date_default():
    return datetime.datetime.now().date()


def timedelta_default():
    return datetime.timedelta(days=1)


def boolean_default():
    return True


def numeric_default():
    return decimal.Decimal("1.2")


def array_default_integer():
    return [4, 5, 6]


def array_default_varchar():
    return ["x", "y", "z"]


class MigrationTestCase(DBTestCase):
    def run_migrations(self, app_config: AppConfig):
        manager = ForwardsMigrationManager(app_name=app_config.app_name)
        run_sync(manager.create_migration_table())
        run_sync(manager.run_migrations(app_config=app_config))

    def _test_migrations(
        self,
        table_snapshots: t.List[t.List[t.Type[Table]]],
        test_function: t.Optional[t.Callable[[RowMeta], None]] = None,
    ):
        """
        Writes a migration file to disk and runs it.

        :param table_snapshots:
            A list of lists. Each sub list represents a snapshot of the table
            state. Migrations will be created and run based each snapshot.
        :param test_function:
            After the migrations are run, this function is called. It is passed
            a ``RowMeta`` instance which can be used to check the column was
            created correctly in the database. It should return ``True`` if the
            test passes, otherwise ``False``.

        """
        temp_directory_path = tempfile.gettempdir()
        migrations_folder_path = os.path.join(
            temp_directory_path, "piccolo_migrations"
        )

        if os.path.exists(migrations_folder_path):
            shutil.rmtree(migrations_folder_path)

        _create_migrations_folder(migrations_folder_path)

        app_config = AppConfig(
            app_name="test_app",
            migrations_folder_path=migrations_folder_path,
            table_classes=[],
        )

        for table_snapshot in table_snapshots:
            app_config.table_classes = table_snapshot
            meta = run_sync(
                _create_new_migration(
                    app_config=app_config, auto=True, auto_input="y"
                )
            )
            self.assertTrue(os.path.exists(meta.migration_path))
            self.run_migrations(app_config=app_config)

            # It's kind of absurd sleeping for 1 microsecond, but it guarantees
            # the migration IDs will be unique, and just in case computers
            # and / or Python get insanely fast in the future :)
            time.sleep(1e-6)

        if test_function:
            column_name = (
                table_snapshots[-1][-1]
                ._meta.non_default_columns[0]
                ._meta.db_column_name
            )
            row_meta = self.get_postgres_column_definition(
                tablename="my_table",
                column_name=column_name,
            )
            self.assertTrue(
                test_function(row_meta),
                msg=f"Meta is incorrect: {row_meta}",
            )


@engines_only("postgres", "cockroach")
class TestMigrations(MigrationTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        create_table_class("MyTable").alter().drop_table(
            if_exists=True
        ).run_sync()
        Migration.alter().drop_table(if_exists=True).run_sync()

    ###########################################################################

    def table(self, column: Column):
        """
        A utility for creating Piccolo tables with the given column.
        """
        return create_table_class(
            class_name="MyTable", class_members={"my_column": column}
        )

    @engines_skip("cockroach")
    def test_varchar_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Varchar(),
                    Varchar(length=100),
                    Varchar(default="hello world"),
                    Varchar(default=string_default),
                    Varchar(null=True),
                    Varchar(null=False),
                    Varchar(index=True),
                    Varchar(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "character varying",
                    x.is_nullable == "NO",
                    x.column_default
                    in ("''::character varying", "'':::STRING"),
                ]
            ),
        )

    def test_text_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Text(),
                    Text(default="hello world"),
                    Text(default=string_default),
                    Text(null=True),
                    Text(null=False),
                    Text(index=True),
                    Text(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "text",
                    x.is_nullable == "NO",
                    x.column_default in ("''::text", "'':::STRING"),
                ]
            ),
        )

    def test_integer_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Integer(),
                    Integer(default=1),
                    Integer(default=integer_default),
                    Integer(null=True),
                    Integer(null=False),
                    Integer(index=True),
                    Integer(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type in ("integer", "bigint"),  # Cockroach DB.
                    x.is_nullable == "NO",
                    x.column_default in ("0", "0:::INT8"),  # Cockroach DB.
                ]
            ),
        )

    def test_real_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Real(),
                    Real(default=1.1),
                    Real(null=True),
                    Real(null=False),
                    Real(index=True),
                    Real(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "real",
                    x.is_nullable == "NO",
                    x.column_default in ("0.0", "0.0:::FLOAT8"),
                ]
            ),
        )

    def test_double_precision_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    DoublePrecision(),
                    DoublePrecision(default=1.1),
                    DoublePrecision(null=True),
                    DoublePrecision(null=False),
                    DoublePrecision(index=True),
                    DoublePrecision(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "double precision",
                    x.is_nullable == "NO",
                    x.column_default in ("0.0", "0.0:::FLOAT8"),
                ]
            ),
        )

    def test_smallint_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    SmallInt(),
                    SmallInt(default=1),
                    SmallInt(default=integer_default),
                    SmallInt(null=True),
                    SmallInt(null=False),
                    SmallInt(index=True),
                    SmallInt(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "smallint",
                    x.is_nullable == "NO",
                    x.column_default in ("0", "0:::INT8"),  # Cockroach DB.
                ]
            ),
        )

    def test_bigint_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    BigInt(),
                    BigInt(default=1),
                    BigInt(default=integer_default),
                    BigInt(null=True),
                    BigInt(null=False),
                    BigInt(index=True),
                    BigInt(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "bigint",
                    x.is_nullable == "NO",
                    x.column_default in ("0", "0:::INT8"),  # Cockroach DB.
                ]
            ),
        )

    def test_uuid_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    UUID(),
                    UUID(default="ecf338cd-6da7-464c-b31e-4b2e3e12f0f0"),
                    UUID(
                        default=uuid.UUID(
                            "2dfc9c47-adab-4692-b804-f692f3b0fc07"
                        )
                    ),
                    UUID(default=uuid.uuid4),
                    UUID(default=uuid_default),
                    UUID(default=UUID4()),
                    UUID(null=True, default=None),
                    UUID(null=False),
                    UUID(index=True),
                    UUID(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "uuid",
                    x.is_nullable == "NO",
                    x.column_default == "uuid_generate_v4()",
                ]
            ),
        )

    def test_timestamp_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Timestamp(),
                    Timestamp(
                        default=datetime.datetime(year=2021, month=1, day=1)
                    ),
                    Timestamp(default=datetime.datetime.now),
                    Timestamp(default=datetime_default),
                    Timestamp(null=True, default=None),
                    Timestamp(null=False),
                    Timestamp(index=True),
                    Timestamp(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "timestamp without time zone",
                    x.is_nullable == "NO",
                    x.column_default
                    in (
                        "now()",
                        "CURRENT_TIMESTAMP",
                        "current_timestamp():::TIMESTAMPTZ::TIMESTAMP",
                    ),
                ]
            ),
        )

    @engines_skip("cockroach")
    def test_time_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Time(),
                    Time(default=datetime.time(hour=12, minute=0)),
                    Time(default=datetime.time),
                    Time(default=time_default),
                    Time(null=True, default=None),
                    Time(null=False),
                    Time(index=True),
                    Time(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "time without time zone",
                    x.is_nullable == "NO",
                    x.column_default
                    in ("('now'::text)::time with time zone", "CURRENT_TIME"),
                ]
            ),
        )

    def test_date_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Date(),
                    Date(default=datetime.date(year=2021, month=1, day=1)),
                    Date(default=datetime.date.today),
                    Date(default=date_default),
                    Date(null=True, default=None),
                    Date(null=False),
                    Date(index=True),
                    Date(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "date",
                    x.is_nullable == "NO",
                    x.column_default
                    in (
                        "('now'::text)::date",
                        "CURRENT_DATE",
                        "current_date()",
                    ),
                ]
            ),
        )

    def test_interval_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Interval(),
                    Interval(default=datetime.timedelta(days=1)),
                    Interval(default=timedelta_default),
                    Interval(null=True, default=None),
                    Interval(null=False),
                    Interval(index=True),
                    Interval(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "interval",
                    x.is_nullable == "NO",
                    x.column_default
                    in ("'00:00:00'::interval", "'00:00:00':::INTERVAL"),
                ]
            ),
        )

    def test_boolean_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Boolean(),
                    Boolean(default=True),
                    Boolean(default=boolean_default),
                    Boolean(null=True, default=None),
                    Boolean(null=False),
                    Boolean(index=True),
                    Boolean(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "boolean",
                    x.is_nullable == "NO",
                    x.column_default == "false",
                ]
            ),
        )

    @engines_skip("cockroach")
    def test_numeric_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Numeric(),
                    Numeric(digits=(4, 2)),
                    Numeric(digits=None),
                    Numeric(default=decimal.Decimal("1.2")),
                    Numeric(default=numeric_default),
                    Numeric(null=True, default=None),
                    Numeric(null=False),
                    Numeric(index=True),
                    Numeric(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "numeric",
                    x.is_nullable == "NO",
                    x.column_default == "0",
                ]
            ),
        )

    @engines_skip("cockroach")
    def test_decimal_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Decimal(),
                    Decimal(digits=(4, 2)),
                    Decimal(digits=None),
                    Decimal(default=decimal.Decimal("1.2")),
                    Decimal(default=numeric_default),
                    Decimal(null=True, default=None),
                    Decimal(null=False),
                    Decimal(index=True),
                    Decimal(index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "numeric",
                    x.is_nullable == "NO",
                    x.column_default == "0",
                ]
            ),
        )

    @engines_skip("cockroach")
    def test_array_column_integer(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/35730 "column my_column is of type int[] and thus is not indexable"
        """  # noqa: E501
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Array(base_column=Integer()),
                    Array(base_column=Integer(), default=[1, 2, 3]),
                    Array(
                        base_column=Integer(), default=array_default_integer
                    ),
                    Array(base_column=Integer(), null=True, default=None),
                    Array(base_column=Integer(), null=False),
                    Array(base_column=Integer(), index=True),
                    Array(base_column=Integer(), index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "ARRAY",
                    x.is_nullable == "NO",
                    x.column_default == "'{}'::integer[]",
                ]
            ),
        )

    @engines_skip("cockroach")
    def test_array_column_varchar(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/35730 "column my_column is of type varchar[] and thus is not indexable"
        """  # noqa: E501
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Array(base_column=Varchar()),
                    Array(base_column=Varchar(), default=["a", "b", "c"]),
                    Array(
                        base_column=Varchar(), default=array_default_varchar
                    ),
                    Array(base_column=Varchar(), null=True, default=None),
                    Array(base_column=Varchar(), null=False),
                    Array(base_column=Varchar(), index=True),
                    Array(base_column=Varchar(), index=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "ARRAY",
                    x.is_nullable == "NO",
                    x.column_default
                    in ("'{}'::character varying[]", "'':::STRING"),
                ]
            ),
        )

    def test_array_column_bigint(self):
        """
        There was a bug with using an array of ``BigInt`` - see issue 500 on
        GitHub. It's because ``BigInt`` requires access to the parent table to
        determine what the column type is.
        """
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Array(base_column=BigInt()),
                ]
            ]
        )

    ###########################################################################

    # We deliberately don't test setting JSON or JSONB columns as indexes, as
    # we know it'll fail.

    @engines_skip("cockroach")
    def test_json_column(self):
        """
        Cockroach sees all json as jsonb, so we can skip this.
        """
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    JSON(),
                    JSON(default=["a", "b", "c"]),
                    JSON(default={"name": "bob"}),
                    JSON(default='{"name": "Sally"}'),
                    JSON(null=True, default=None),
                    JSON(null=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "json",
                    x.is_nullable == "NO",
                    x.column_default == "'{}'::json",
                ]
            ),
        )

    def test_jsonb_column(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    JSONB(),
                    JSONB(default=["a", "b", "c"]),
                    JSONB(default={"name": "bob"}),
                    JSONB(default='{"name": "Sally"}'),
                    JSONB(null=True, default=None),
                    JSONB(null=False),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "jsonb",
                    x.is_nullable == "NO",
                    x.column_default in ("'{}'::jsonb", "'{}':::JSONB"),
                ]
            ),
        )

    ###########################################################################

    def test_db_column_name(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Varchar(),
                    Varchar(db_column_name="custom_name"),
                    Varchar(),
                    Varchar(db_column_name="custom_name_2"),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "character varying",
                    x.is_nullable == "NO",
                    x.column_default
                    in ("''::character varying", "'':::STRING"),
                ]
            ),
        )

    def test_db_column_name_initial(self):
        """
        Make sure that if a new table is created which contains a column with
        ``db_column_name`` specified, then the column has the correct name.
        """
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Varchar(db_column_name="custom_name"),
                ]
            ],
            test_function=lambda x: all(
                [
                    x.data_type == "character varying",
                    x.is_nullable == "NO",
                    x.column_default
                    in ("''::character varying", "'':::STRING"),
                ]
            ),
        )

    ###########################################################################

    # Column type conversion

    def test_column_type_conversion_string(self):
        """
        We can't manage all column type conversions, but should be able to
        manage most simple ones (e.g. Varchar to Text).
        """
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Varchar(),
                    Text(),
                    Varchar(),
                ]
            ]
        )

    @engines_skip("cockroach")
    def test_column_type_conversion_integer(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/49351 "ALTER COLUMN TYPE is not supported inside a transaction"
        """  # noqa: E501
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Integer(),
                    BigInt(),
                    SmallInt(),
                    BigInt(),
                    Integer(),
                ]
            ]
        )

    @engines_skip("cockroach")
    def test_column_type_conversion_string_to_integer(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/49351 "ALTER COLUMN TYPE is not supported inside a transaction"
        """  # noqa: E501
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Varchar(default="1"),
                    Integer(default=1),
                    Varchar(default="1"),
                ]
            ]
        )

    @engines_skip("cockroach")
    def test_column_type_conversion_float_decimal(self):
        """
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/49351 "ALTER COLUMN TYPE is not supported inside a transaction"
        """  # noqa: E501
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Real(default=1.0),
                    DoublePrecision(default=1.0),
                    Real(default=1.0),
                    Numeric(),
                    Real(default=1.0),
                ]
            ]
        )

    def test_column_type_conversion_json(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    JSON(),
                    JSONB(),
                    JSON(),
                ]
            ]
        )

    def test_column_type_conversion_timestamp(self):
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Timestamp(),
                    Timestamptz(),
                    Timestamp(),
                ]
            ]
        )

    @patch("piccolo.apps.migrations.auto.migration_manager.colored_warning")
    def test_column_type_conversion_serial(self, colored_warning: MagicMock):
        """
        This isn't possible, as neither SERIAL or BIGSERIAL are actual types.
        They're just shortcuts. Make sure the migration doesn't crash - it
        should just output a warning.
        """
        self._test_migrations(
            table_snapshots=[
                [self.table(column)]
                for column in [
                    Serial(),
                    BigSerial(),
                ]
            ]
        )

        colored_warning.assert_called_once_with(
            "Unable to migrate Serial to BigSerial and vice versa. This must "
            "be done manually."
        )


###############################################################################


class Band(Table):
    name = Varchar()
    genres = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class Genre(Table):
    name = Varchar()
    bands = M2M(LazyTableReference("GenreToBand", module_path=__name__))


class GenreToBand(Table):
    band = ForeignKey(Band)
    genre = ForeignKey(Genre)


@engines_only("postgres", "cockroach")
class TestM2MMigrations(MigrationTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        drop_db_tables_sync(Migration, Band, Genre, GenreToBand)

    def test_m2m(self):
        """
        Make sure M2M relations can be created.
        """

        self._test_migrations(
            table_snapshots=[[Band, Genre, GenreToBand]],
        )

        for table_class in [Band, Genre, GenreToBand]:
            self.assertTrue(table_class.table_exists().run_sync())


###############################################################################


@engines_only("postgres", "cockroach")
class TestForeignKeys(MigrationTestCase):
    def setUp(self):
        class TableA(Table):
            pass

        class TableB(Table):
            fk = ForeignKey(TableA)

        class TableC(Table):
            fk = ForeignKey(TableB)

        class TableD(Table):
            fk = ForeignKey(TableC)

        class TableE(Table):
            fk = ForeignKey(TableD)

        self.table_classes = [TableA, TableB, TableC, TableD, TableE]

    def tearDown(self):
        drop_db_tables_sync(Migration, *self.table_classes)

    def test_foreign_keys(self):
        """
        Make sure that if we try creating tables with lots of foreign keys
        to each other it runs successfully.

        https://github.com/piccolo-orm/piccolo/issues/616

        """
        # We'll shuffle them, to make it a more thorough test.
        table_classes = random.sample(
            self.table_classes, len(self.table_classes)
        )

        self._test_migrations(table_snapshots=[table_classes])
        for table_class in table_classes:
            self.assertTrue(table_class.table_exists().run_sync())


@engines_only("postgres", "cockroach")
class TestTargetColumn(MigrationTestCase):
    def setUp(self):
        class TableA(Table):
            name = Varchar(unique=True)

        class TableB(Table):
            table_a = ForeignKey(TableA, target_column=TableA.name)

        self.table_classes = [TableA, TableB]

    def tearDown(self):
        drop_db_tables_sync(Migration, *self.table_classes)

    def test_target_column(self):
        """
        Make sure migrations still work when a foreign key references a column
        other than the primary key.
        """
        self._test_migrations(
            table_snapshots=[self.table_classes],
        )

        for table_class in self.table_classes:
            self.assertTrue(table_class.table_exists().run_sync())

        # Make sure the constraint was created correctly.
        response = self.run_sync(
            """
            SELECT EXISTS(
                SELECT 1
                FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE CCU
                JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC ON
                    CCU.CONSTRAINT_NAME = TC.CONSTRAINT_NAME
                WHERE CONSTRAINT_TYPE = 'FOREIGN KEY'
                    AND TC.TABLE_NAME = 'table_b'
                    AND CCU.TABLE_NAME = 'table_a'
                    AND CCU.COLUMN_NAME = 'name'
            )
            """
        )
        self.assertTrue(response[0]["exists"])


@engines_only("postgres", "cockroach")
class TestTargetColumnString(MigrationTestCase):
    def setUp(self):
        class TableA(Table):
            name = Varchar(unique=True)

        class TableB(Table):
            table_a = ForeignKey(TableA, target_column="name")

        self.table_classes = [TableA, TableB]

    def tearDown(self):
        drop_db_tables_sync(Migration, *self.table_classes)

    def test_target_column(self):
        """
        Make sure migrations still work when a foreign key references a column
        other than the primary key.
        """
        self._test_migrations(
            table_snapshots=[self.table_classes],
        )

        for table_class in self.table_classes:
            self.assertTrue(table_class.table_exists().run_sync())

        # Make sure the constraint was created correctly.
        response = self.run_sync(
            """
            SELECT EXISTS(
                SELECT 1
                FROM INFORMATION_SCHEMA.CONSTRAINT_COLUMN_USAGE CCU
                JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC ON
                    CCU.CONSTRAINT_NAME = TC.CONSTRAINT_NAME
                WHERE CONSTRAINT_TYPE = 'FOREIGN KEY'
                    AND TC.TABLE_NAME = 'table_b'
                    AND CCU.TABLE_NAME = 'table_a'
                    AND CCU.COLUMN_NAME = 'name'
            )
            """
        )
        self.assertTrue(response[0]["exists"])
