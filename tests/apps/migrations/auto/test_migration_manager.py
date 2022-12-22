import asyncio
import random
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.apps.migrations.commands.base import BaseMigrationManager
from piccolo.columns import Text, Varchar
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.columns.column_types import ForeignKey
from piccolo.conf.apps import AppConfig
from piccolo.table import Table, sort_table_classes
from piccolo.utils.lazy_loader import LazyLoader
from tests.base import AsyncMock, DBTestCase, engine_is, engines_only
from tests.example_apps.music.tables import Band, Concert, Manager, Venue

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")


class TestSortTableClasses(TestCase):
    def test_sort_table_classes(self):
        """
        Make sure simple use cases work correctly.
        """
        self.assertListEqual(
            sort_table_classes([Manager, Band]), [Manager, Band]
        )
        self.assertListEqual(
            sort_table_classes([Band, Manager]), [Manager, Band]
        )

        sorted_tables = sort_table_classes([Manager, Venue, Concert, Band])
        self.assertTrue(
            sorted_tables.index(Manager) < sorted_tables.index(Band)
        )
        self.assertTrue(
            sorted_tables.index(Venue) < sorted_tables.index(Concert)
        )
        self.assertTrue(
            sorted_tables.index(Band) < sorted_tables.index(Concert)
        )

    def test_sort_unrelated_tables(self):
        """
        Make sure there are no weird edge cases with tables with no foreign
        key relationships with each other.
        """

        class TableA(Table):
            pass

        class TableB(Table):
            pass

        self.assertListEqual(
            sort_table_classes([TableA, TableB]), [TableA, TableB]
        )

    def test_single_table(self):
        """
        Make sure that sorting a list with only a single table in it still
        works.
        """
        self.assertListEqual(sort_table_classes([Band]), [Band])

    def test_recursive_table(self):
        """
        Make sure that a table with a foreign key to itself sorts without
        issues.
        """

        class TableA(Table):
            table_a = ForeignKey("self")

        class TableB(Table):
            table_a = ForeignKey(TableA)

        self.assertListEqual(
            sort_table_classes([TableA, TableB]), [TableA, TableB]
        )

    def test_long_chain(self):
        """
        Make sure sorting works when there are a lot of tables with foreign
        keys to each other.

        https://github.com/piccolo-orm/piccolo/issues/616

        """

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

        tables = [TableA, TableB, TableC, TableD, TableE]

        shuffled_tables = random.sample(tables, len(tables))

        self.assertListEqual(sort_table_classes(shuffled_tables), tables)


class TestMigrationManager(DBTestCase):
    @engines_only("postgres", "cockroach")
    def test_rename_column(self):
        """
        Test running a MigrationManager which contains a column rename
        operation.
        """
        self.insert_row()

        manager = MigrationManager()
        manager.rename_column(
            table_class_name="Band",
            tablename="band",
            old_column_name="name",
            new_column_name="title",
        )
        asyncio.run(manager.run())

        response = self.run_sync("SELECT * FROM band;")
        self.assertTrue("title" in response[0].keys())
        self.assertTrue("name" not in response[0].keys())

        # Reverse
        asyncio.run(manager.run(backwards=True))
        response = self.run_sync("SELECT * FROM band;")
        self.assertTrue("title" not in response[0].keys())
        self.assertTrue("name" in response[0].keys())

        # Preview
        manager.preview = True
        with patch("sys.stdout", new=StringIO()) as fake_out:
            asyncio.run(manager.run())
            self.assertEqual(
                fake_out.getvalue(),
                """  -  [preview forwards]... \n ALTER TABLE band RENAME COLUMN "name" TO "title";\n""",  # noqa: E501
            )
        response = self.run_sync("SELECT * FROM band;")
        self.assertTrue("title" not in response[0].keys())
        self.assertTrue("name" in response[0].keys())

    def test_raw_function(self):
        """
        Test adding raw functions to a MigrationManager.
        """

        class HasRun(Exception):
            pass

        class HasRunBackwards(Exception):
            pass

        def run():
            raise HasRun("I was run!")

        def run_back():
            raise HasRunBackwards("I was run backwards!")

        manager = MigrationManager()
        manager.add_raw(run)
        manager.add_raw_backwards(run_back)

        with self.assertRaises(HasRun):
            asyncio.run(manager.run())

        # Reverse
        with self.assertRaises(HasRunBackwards):
            asyncio.run(manager.run(backwards=True))

    def test_raw_coroutine(self):
        """
        Test adding raw coroutines to a MigrationManager.
        """

        class HasRun(Exception):
            pass

        class HasRunBackwards(Exception):
            pass

        async def run():
            raise HasRun("I was run!")

        async def run_back():
            raise HasRunBackwards("I was run backwards!")

        manager = MigrationManager()
        manager.add_raw(run)
        manager.add_raw_backwards(run_back)

        with self.assertRaises(HasRun):
            asyncio.run(manager.run())

        # Reverse
        with self.assertRaises(HasRunBackwards):
            asyncio.run(manager.run(backwards=True))

    @engines_only("postgres", "cockroach")
    @patch.object(BaseMigrationManager, "get_app_config")
    def test_add_table(self, get_app_config: MagicMock):
        """
        Test adding a table to a MigrationManager.
        """
        self.run_sync("DROP TABLE IF EXISTS musician;")

        manager = MigrationManager()
        manager.add_table(class_name="Musician", tablename="musician")
        manager.add_column(
            table_class_name="Musician",
            tablename="musician",
            column_name="name",
            column_class_name="Varchar",
        )
        asyncio.run(manager.run())

        if engine_is("postgres"):
            self.run_sync(
                "INSERT INTO musician VALUES (default, 'Bob Jones');"
            )
            response = self.run_sync("SELECT * FROM musician;")
            self.assertEqual(response, [{"id": 1, "name": "Bob Jones"}])

        if engine_is("cockroach"):
            id = self.run_sync(
                "INSERT INTO musician VALUES (default, 'Bob Jones') RETURNING id;"  # noqa: E501
            )
            response = self.run_sync("SELECT * FROM musician;")
            self.assertEqual(
                response, [{"id": id[0]["id"], "name": "Bob Jones"}]
            )
        # Reverse

        get_app_config.return_value = AppConfig(
            app_name="music", migrations_folder_path=""
        )
        asyncio.run(manager.run(backwards=True))
        self.assertEqual(self.table_exists("musician"), False)
        self.run_sync("DROP TABLE IF EXISTS musician;")

        # Preview
        manager.preview = True
        with patch("sys.stdout", new=StringIO()) as fake_out:
            asyncio.run(manager.run())

            if engine_is("postgres"):
                self.assertEqual(
                    fake_out.getvalue(),
                    """  -  [preview forwards]... \n CREATE TABLE musician ("id" SERIAL PRIMARY KEY NOT NULL, "name" VARCHAR(255) NOT NULL DEFAULT '');\n""",  # noqa: E501
                )
            if engine_is("cockroach"):
                self.assertEqual(
                    fake_out.getvalue(),
                    """  -  [preview forwards]... \n CREATE TABLE musician ("id" INTEGER PRIMARY KEY NOT NULL DEFAULT unique_rowid(), "name" VARCHAR(255) NOT NULL DEFAULT '');\n""",  # noqa: E501
                )
        self.assertEqual(self.table_exists("musician"), False)

    @engines_only("postgres", "cockroach")
    def test_add_column(self):
        """
        Test adding a column to a MigrationManager.
        """
        manager = MigrationManager()
        manager.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="email",
            column_class=Varchar,
            column_class_name="Varchar",
            params={
                "length": 100,
                "default": "",
                "null": True,
                "primary": False,
                "key": False,
                "unique": True,
                "index": False,
            },
        )
        asyncio.run(manager.run())

        if engine_is("postgres"):
            self.run_sync(
                "INSERT INTO manager VALUES (default, 'Dave', 'dave@me.com');"
            )
            response = self.run_sync("SELECT * FROM manager;")
            self.assertEqual(
                response, [{"id": 1, "name": "Dave", "email": "dave@me.com"}]
            )

            # Reverse
            asyncio.run(manager.run(backwards=True))
            response = self.run_sync("SELECT * FROM manager;")
            self.assertEqual(response, [{"id": 1, "name": "Dave"}])

        id = 0
        if engine_is("cockroach"):
            id = self.run_sync(
                "INSERT INTO manager VALUES (default, 'Dave', 'dave@me.com') RETURNING id;"  # noqa: E501
            )
            response = self.run_sync("SELECT * FROM manager;")
            self.assertEqual(
                response,
                [{"id": id[0]["id"], "name": "Dave", "email": "dave@me.com"}],
            )

            # Reverse
            asyncio.run(manager.run(backwards=True))
            response = self.run_sync("SELECT * FROM manager;")
            self.assertEqual(response, [{"id": id[0]["id"], "name": "Dave"}])

        # Preview
        manager.preview = True
        with patch("sys.stdout", new=StringIO()) as fake_out:
            asyncio.run(manager.run())
            self.assertEqual(
                fake_out.getvalue(),
                """  -  [preview forwards]... \n ALTER TABLE manager ADD COLUMN "email" VARCHAR(100) UNIQUE DEFAULT '';\n""",  # noqa: E501
            )

        response = self.run_sync("SELECT * FROM manager;")
        if engine_is("postgres"):
            self.assertEqual(response, [{"id": 1, "name": "Dave"}])
        if engine_is("cockroach"):
            self.assertEqual(response, [{"id": id[0]["id"], "name": "Dave"}])

    @engines_only("postgres", "cockroach")
    def test_add_column_with_index(self):
        """
        Test adding a column with an index to a MigrationManager.
        """
        manager = MigrationManager()
        manager.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="email",
            column_class=Varchar,
            column_class_name="Varchar",
            params={
                "length": 100,
                "default": "",
                "null": True,
                "primary": False,
                "key": False,
                "unique": True,
                "index": True,
            },
        )
        index_name = Manager._get_index_name(["email"])

        asyncio.run(manager.run())
        self.assertTrue(index_name in Manager.indexes().run_sync())

        # Reverse
        asyncio.run(manager.run(backwards=True))
        self.assertTrue(index_name not in Manager.indexes().run_sync())

        # Preview
        manager.preview = True
        with patch("sys.stdout", new=StringIO()) as fake_out:
            asyncio.run(manager.run())
            self.assertEqual(
                fake_out.getvalue(),
                (
                    """  -  [preview forwards]... \n ALTER TABLE manager ADD COLUMN "email" VARCHAR(100) UNIQUE DEFAULT '';\n"""  # noqa: E501
                    """\n CREATE INDEX manager_email ON manager USING btree ("email");\n"""  # noqa: E501
                ),
            )
        self.assertTrue(index_name not in Manager.indexes().run_sync())

    @engines_only("postgres")
    def test_add_foreign_key_self_column(self):
        """
        Test adding a ForeignKey column to a MigrationManager, with a
        references argument of 'self'.
        """
        manager = MigrationManager()
        manager.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="advisor",
            column_class=ForeignKey,
            column_class_name="ForeignKey",
            params={
                "references": "self",
                "on_delete": OnDelete.cascade,
                "on_update": OnUpdate.cascade,
                "default": None,
                "null": True,
                "primary": False,
                "key": False,
                "unique": False,
                "index": False,
            },
        )
        asyncio.run(manager.run())

        self.run_sync("INSERT INTO manager VALUES (default, 'Alice', null);")
        self.run_sync("INSERT INTO manager VALUES (default, 'Dave', 1);")

        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(
            response,
            [
                {"id": 1, "name": "Alice", "advisor": None},
                {"id": 2, "name": "Dave", "advisor": 1},
            ],
        )

        # Reverse
        asyncio.run(manager.run(backwards=True))
        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(
            response,
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Dave"}],
        )

    @engines_only("cockroach")
    def test_add_foreign_key_self_column_alt(self):
        """
        Test adding a ForeignKey column to a MigrationManager, with a
        references argument of 'self'.
        """
        manager = MigrationManager()
        manager.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="advisor",
            column_class=ForeignKey,
            column_class_name="ForeignKey",
            params={
                "references": "self",
                "on_delete": OnDelete.cascade,
                "on_update": OnUpdate.cascade,
                "default": None,
                "null": True,
                "primary": False,
                "key": False,
                "unique": False,
                "index": False,
            },
        )
        asyncio.run(manager.run())

        id = self.run_sync(
            "INSERT INTO manager VALUES (default, 'Alice', null) RETURNING id;"
        )
        id2 = Manager.raw(
            "INSERT INTO manager VALUES (default, 'Dave', {}) RETURNING id;",
            id[0]["id"],
        ).run_sync()

        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(
            response,
            [
                {"id": id[0]["id"], "name": "Alice", "advisor": None},
                {"id": id2[0]["id"], "name": "Dave", "advisor": id[0]["id"]},
            ],
        )

        # Reverse
        asyncio.run(manager.run(backwards=True))
        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(
            response,
            [
                {"id": id[0]["id"], "name": "Alice"},
                {"id": id2[0]["id"], "name": "Dave"},
            ],
        )

    @engines_only("postgres", "cockroach")
    def test_add_non_nullable_column(self):
        """
        Test adding a non nullable column to a MigrationManager.

        Need to handle it gracefully if rows already exist.
        """
        self.run_sync("INSERT INTO manager VALUES (default, 'Dave');")

        manager = MigrationManager()
        manager.add_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="email",
            column_class=Varchar,
            column_class_name="Varchar",
            params={
                "length": 100,
                "default": "",
                "null": False,
                "primary": False,
                "key": False,
                "unique": True,
                "index": False,
            },
        )
        asyncio.run(manager.run())

    @engines_only("postgres", "cockroach")
    @patch.object(
        BaseMigrationManager, "get_migration_managers", new_callable=AsyncMock
    )
    @patch.object(BaseMigrationManager, "get_app_config")
    def test_drop_column(
        self, get_app_config: MagicMock, get_migration_managers: MagicMock
    ):
        """
        Test dropping a column with MigrationManager.
        """
        manager_1 = MigrationManager()
        manager_1.add_table(class_name="Musician", tablename="musician")
        manager_1.add_column(
            table_class_name="Musician",
            tablename="musician",
            column_name="name",
            column_class_name="Varchar",
        )
        asyncio.run(manager_1.run())

        if engine_is("postgres"):
            self.run_sync("INSERT INTO musician VALUES (default, 'Dave');")
            response = self.run_sync("SELECT * FROM musician;")
            self.assertEqual(response, [{"id": 1, "name": "Dave"}])

        id = 0
        if engine_is("cockroach"):
            id = self.run_sync(
                "INSERT INTO musician VALUES (default, 'Dave') RETURNING id;"
            )
            response = self.run_sync("SELECT * FROM musician;")
            self.assertEqual(
                response, [{"id": id[0]["id"], "name": "Dave"}]  # type: ignore
            )

        manager_2 = MigrationManager()
        manager_2.drop_column(
            table_class_name="Musician",
            tablename="musician",
            column_name="name",
        )
        asyncio.run(manager_2.run())

        if engine_is("postgres"):
            response = self.run_sync("SELECT * FROM musician;")
            self.assertEqual(response, [{"id": 1}])

        if engine_is("cockroach"):
            response = self.run_sync("SELECT * FROM musician;")
            self.assertEqual(response, [{"id": id[0]["id"]}])  # type: ignore

        # Reverse
        get_migration_managers.return_value = [manager_1]
        app_config = AppConfig(app_name="music", migrations_folder_path="")
        get_app_config.return_value = app_config
        asyncio.run(manager_2.run(backwards=True))
        response = self.run_sync("SELECT * FROM musician;")
        if engine_is("postgres"):
            self.assertEqual(response, [{"id": 1, "name": ""}])

        if engine_is("cockroach"):
            self.assertEqual(
                response, [{"id": id[0]["id"], "name": ""}]  # type: ignore
            )

    @engines_only("postgres", "cockroach")
    def test_rename_table(self):
        """
        Test renaming a table with MigrationManager.
        """
        manager = MigrationManager()

        manager.rename_table(
            old_class_name="Manager",
            old_tablename="manager",
            new_class_name="Director",
            new_tablename="director",
        )

        asyncio.run(manager.run())

        if engine_is("postgres"):
            self.run_sync("INSERT INTO director VALUES (default, 'Dave');")

            response = self.run_sync("SELECT * FROM director;")
            self.assertEqual(response, [{"id": 1, "name": "Dave"}])

            # Reverse
            asyncio.run(manager.run(backwards=True))
            response = self.run_sync("SELECT * FROM manager;")
            self.assertEqual(response, [{"id": 1, "name": "Dave"}])

        if engine_is("cockroach"):
            id = 0
            id = self.run_sync(
                "INSERT INTO director VALUES (default, 'Dave') RETURNING id;"
            )

            response = self.run_sync("SELECT * FROM director;")
            self.assertEqual(response, [{"id": id[0]["id"], "name": "Dave"}])

            # Reverse
            asyncio.run(manager.run(backwards=True))
            response = self.run_sync("SELECT * FROM manager;")
            self.assertEqual(response, [{"id": id[0]["id"], "name": "Dave"}])

    @engines_only("postgres")
    def test_alter_column_unique(self):
        """
        Test altering a column uniqueness with MigrationManager.
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/42840 "unimplemented: cannot drop UNIQUE constraint "manager_name_key" using ALTER TABLE DROP CONSTRAINT, use DROP INDEX CASCADE instead"
        """  # noqa: E501
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"unique": True},
            old_params={"unique": False},
        )

        asyncio.run(manager.run())

        with self.assertRaises(asyncpg.exceptions.UniqueViolationError):
            self.run_sync(
                "INSERT INTO manager VALUES "
                "(default, 'Dave'), (default, 'Dave');"
            )

        # Reverse
        asyncio.run(manager.run(backwards=True))
        self.run_sync(
            "INSERT INTO manager VALUES (default, 'Dave'), (default, 'Dave');"
        )
        response = self.run_sync("SELECT name FROM manager;")
        self.assertEqual(response, [{"name": "Dave"}, {"name": "Dave"}])

    @engines_only("postgres", "cockroach")
    def test_alter_column_set_null(self):
        """
        Test altering whether a column is nullable with MigrationManager.
        """
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"null": True},
            old_params={"null": False},
        )

        asyncio.run(manager.run())
        self.assertTrue(
            self.get_postgres_is_nullable(
                tablename="manager", column_name="name"
            )
        )

        # Reverse
        asyncio.run(manager.run(backwards=True))
        self.assertFalse(
            self.get_postgres_is_nullable(
                tablename="manager", column_name="name"
            )
        )

    def _get_column_precision_and_scale(
        self, tablename="ticket", column_name="price"
    ):
        return self.run_sync(
            "SELECT numeric_precision, numeric_scale "
            "FROM information_schema.COLUMNS "
            f"WHERE table_name = '{tablename}' AND "
            f"column_name = '{column_name}';"
        )

    def _get_column_default(self, tablename="manager", column_name="name"):
        return self.run_sync(
            "SELECT column_default "
            "FROM information_schema.COLUMNS "
            f"WHERE table_name = '{tablename}' "
            f"AND column_name = '{column_name}';"
        )

    @engines_only("postgres")
    def test_alter_column_digits(self):
        """
        Test altering a column digits with MigrationManager.
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/49351 "ALTER COLUMN TYPE is not supported inside a transaction"
        """  # noqa: E501
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Ticket",
            tablename="ticket",
            column_name="price",
            params={"digits": (6, 2)},
            old_params={"digits": (5, 2)},
        )

        asyncio.run(manager.run())
        self.assertEqual(
            self._get_column_precision_and_scale(),
            [{"numeric_precision": 6, "numeric_scale": 2}],
        )

        asyncio.run(manager.run(backwards=True))
        self.assertEqual(
            self._get_column_precision_and_scale(),
            [{"numeric_precision": 5, "numeric_scale": 2}],
        )

    @engines_only("postgres")
    def test_alter_column_set_default(self):
        """
        Test altering a column default with MigrationManager.
        """
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"default": "Unknown"},
            old_params={"default": ""},
        )

        asyncio.run(manager.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Unknown'::character varying"}],
        )

        asyncio.run(manager.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "''::character varying"}],
        )

    @engines_only("cockroach")
    def test_alter_column_set_default_alt(self):
        """
        Test altering a column default with MigrationManager.
        """
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"default": "Unknown"},
            old_params={"default": ""},
        )

        asyncio.run(manager.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Unknown':::STRING"}],
        )

        asyncio.run(manager.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'':::STRING"}],
        )

    @engines_only("postgres")
    def test_alter_column_drop_default(self):
        """
        Test setting a column default to None with MigrationManager.
        """
        # Make sure it has a non-null default to start with.
        manager_1 = MigrationManager()
        manager_1.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"default": "Mr Manager"},
            old_params={"default": None},
        )
        asyncio.run(manager_1.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager'::character varying"}],
        )

        # Drop the default.
        manager_2 = MigrationManager()
        manager_2.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"default": None},
            old_params={"default": "Mr Manager"},
        )
        asyncio.run(manager_2.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

        # And add it back once more to be sure.
        manager_3 = manager_1
        asyncio.run(manager_3.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager'::character varying"}],
        )

        # Run them all backwards
        asyncio.run(manager_3.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

        asyncio.run(manager_2.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager'::character varying"}],
        )

        asyncio.run(manager_1.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

    @engines_only("cockroach")
    def test_alter_column_drop_default_alt(self):
        """
        Test setting a column default to None with MigrationManager.
        """
        # Make sure it has a non-null default to start with.
        manager_1 = MigrationManager()
        manager_1.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"default": "Mr Manager"},
            old_params={"default": None},
        )
        asyncio.run(manager_1.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager':::STRING"}],
        )

        # Drop the default.
        manager_2 = MigrationManager()
        manager_2.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"default": None},
            old_params={"default": "Mr Manager"},
        )
        asyncio.run(manager_2.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

        # And add it back once more to be sure.
        manager_3 = manager_1
        asyncio.run(manager_3.run())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager':::STRING"}],
        )

        # Run them all backwards
        asyncio.run(manager_3.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

        asyncio.run(manager_2.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager':::STRING"}],
        )

        asyncio.run(manager_1.run(backwards=True))
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

    @engines_only("postgres", "cockroach")
    def test_alter_column_add_index(self):
        """
        Test altering a column to add an index with MigrationManager.
        """
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"index": True},
            old_params={"index": False},
        )

        asyncio.run(manager.run())
        self.assertTrue(
            Manager._get_index_name(["name"]) in Manager.indexes().run_sync()
        )

        asyncio.run(manager.run(backwards=True))
        self.assertTrue(
            Manager._get_index_name(["name"])
            not in Manager.indexes().run_sync()
        )

    @engines_only("postgres", "cockroach")
    def test_alter_column_set_type(self):
        """
        Test altering a column to change it's type with MigrationManager.
        """
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={},
            old_params={},
            column_class=Text,
            old_column_class=Varchar,
        )

        asyncio.run(manager.run())
        column_type_str = self.get_postgres_column_type(
            tablename="manager", column_name="name"
        )
        self.assertEqual(column_type_str, "TEXT")

        asyncio.run(manager.run(backwards=True))
        column_type_str = self.get_postgres_column_type(
            tablename="manager", column_name="name"
        )
        self.assertEqual(column_type_str, "CHARACTER VARYING")

    @engines_only("postgres")
    def test_alter_column_set_length(self):
        """
        Test altering a Varchar column's length with MigrationManager.
        🐛 Cockroach bug: https://github.com/cockroachdb/cockroach/issues/49351 "ALTER COLUMN TYPE is not supported inside a transaction"
        """  # noqa: E501
        manager = MigrationManager()

        manager.alter_column(
            table_class_name="Manager",
            tablename="manager",
            column_name="name",
            params={"length": 500},
            old_params={"length": 200},
            column_class=Text,
            old_column_class=Varchar,
        )

        asyncio.run(manager.run())
        self.assertEqual(
            self.get_postgres_varchar_length(
                tablename="manager", column_name="name"
            ),
            500,
        )

        asyncio.run(manager.run(backwards=True))
        self.assertEqual(
            self.get_postgres_varchar_length(
                tablename="manager", column_name="name"
            ),
            200,
        )

    @engines_only("postgres", "cockroach")
    @patch.object(
        BaseMigrationManager, "get_migration_managers", new_callable=AsyncMock
    )
    @patch.object(BaseMigrationManager, "get_app_config")
    def test_drop_table(
        self, get_app_config: MagicMock, get_migration_managers: MagicMock
    ):
        self.run_sync("DROP TABLE IF EXISTS musician;")

        name_column = Varchar()
        name_column._meta.name = "name"

        manager_1 = MigrationManager(migration_id="1", app_name="music")
        manager_1.add_table(
            class_name="Musician", tablename="musician", columns=[name_column]
        )
        asyncio.run(manager_1.run())

        manager_2 = MigrationManager(migration_id="2", app_name="music")
        manager_2.drop_table(class_name="Musician", tablename="musician")
        asyncio.run(manager_2.run())

        self.assertTrue(not self.table_exists("musician"))

        # Reverse
        get_migration_managers.return_value = [manager_1]
        app_config = AppConfig(app_name="music", migrations_folder_path="")
        get_app_config.return_value = app_config
        asyncio.run(manager_2.run(backwards=True))

        get_migration_managers.assert_called_with(
            app_config=app_config, max_migration_id="2", offset=-1
        )
        self.assertTrue(self.table_exists("musician"))

        self.run_sync("DROP TABLE IF EXISTS musician;")
