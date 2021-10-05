import asyncio
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
from tests.base import DBTestCase, postgres_only, set_mock_return_value
from tests.example_apps.music.tables import Band, Concert, Manager, Venue

asyncpg = LazyLoader("asyncpg", globals(), "asyncpg")


class TestSortTableClasses(TestCase):
    def test_sort_table_classes(self):
        self.assertEqual(sort_table_classes([Manager, Band]), [Manager, Band])
        self.assertEqual(sort_table_classes([Band, Manager]), [Manager, Band])

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

        self.assertEqual(
            sort_table_classes([TableA, TableB]), [TableA, TableB]
        )

    def test_single_table(self):
        """
        Make sure that sorting a list with only a single table in it still
        works.
        """
        self.assertEqual(sort_table_classes([Band]), [Band])

    def test_recursive_table(self):
        """
        Make sure that a table with a foreign key to itself sorts without
        issues.
        """

        class TableA(Table):
            table_a = ForeignKey("self")

        class TableB(Table):
            table_a = ForeignKey(TableA)

        self.assertEqual(
            sort_table_classes([TableA, TableB]), [TableA, TableB]
        )


class TestMigrationManager(DBTestCase):
    @postgres_only
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
        asyncio.run(manager.run_backwards())
        response = self.run_sync("SELECT * FROM band;")
        self.assertTrue("title" not in response[0].keys())
        self.assertTrue("name" in response[0].keys())

    def test_raw_function(self):
        """
        Test adding raw functions to a MigrationManager.
        """

        class HasRun(Exception):
            pass

        def run():
            raise HasRun("I was run!")

        manager = MigrationManager()
        manager.add_raw(run)
        manager.add_raw_backwards(run)

        with self.assertRaises(HasRun):
            asyncio.run(manager.run())

        # Reverse
        with self.assertRaises(HasRun):
            asyncio.run(manager.run_backwards())

    def test_raw_coroutine(self):
        """
        Test adding raw coroutines to a MigrationManager.
        """

        class HasRun(Exception):
            pass

        async def run():
            raise HasRun("I was run!")

        manager = MigrationManager()
        manager.add_raw(run)
        manager.add_raw_backwards(run)

        with self.assertRaises(HasRun):
            asyncio.run(manager.run())

        # Reverse
        with self.assertRaises(HasRun):
            asyncio.run(manager.run_backwards())

    @postgres_only
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

        self.run_sync("INSERT INTO musician VALUES (default, 'Bob Jones');")
        response = self.run_sync("SELECT * FROM musician;")

        self.assertEqual(response, [{"id": 1, "name": "Bob Jones"}])

        # Reverse

        get_app_config.return_value = AppConfig(
            app_name="music", migrations_folder_path=""
        )
        asyncio.run(manager.run_backwards())
        self.assertEqual(self.table_exists("musician"), False)
        self.run_sync("DROP TABLE IF EXISTS musician;")

    @postgres_only
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

        self.run_sync(
            "INSERT INTO manager VALUES (default, 'Dave', 'dave@me.com');"
        )

        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(
            response, [{"id": 1, "name": "Dave", "email": "dave@me.com"}]
        )

        # Reverse
        asyncio.run(manager.run_backwards())
        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(response, [{"id": 1, "name": "Dave"}])

    @postgres_only
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
        asyncio.run(manager.run_backwards())
        self.assertTrue(index_name not in Manager.indexes().run_sync())

    @postgres_only
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
        asyncio.run(manager.run_backwards())
        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(
            response,
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Dave"}],
        )

    @postgres_only
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

    @postgres_only
    @patch.object(BaseMigrationManager, "get_migration_managers")
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

        self.run_sync("INSERT INTO musician VALUES (default, 'Dave');")
        response = self.run_sync("SELECT * FROM musician;")
        self.assertEqual(response, [{"id": 1, "name": "Dave"}])

        manager_2 = MigrationManager()
        manager_2.drop_column(
            table_class_name="Musician",
            tablename="musician",
            column_name="name",
        )
        asyncio.run(manager_2.run())

        response = self.run_sync("SELECT * FROM musician;")
        self.assertEqual(response, [{"id": 1}])

        # Reverse
        set_mock_return_value(get_migration_managers, [manager_1])
        app_config = AppConfig(app_name="music", migrations_folder_path="")
        get_app_config.return_value = app_config
        asyncio.run(manager_2.run_backwards())
        response = self.run_sync("SELECT * FROM musician;")
        self.assertEqual(response, [{"id": 1, "name": ""}])

    @postgres_only
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

        self.run_sync("INSERT INTO director VALUES (default, 'Dave');")

        response = self.run_sync("SELECT * FROM director;")
        self.assertEqual(response, [{"id": 1, "name": "Dave"}])

        # Reverse
        asyncio.run(manager.run_backwards())
        response = self.run_sync("SELECT * FROM manager;")
        self.assertEqual(response, [{"id": 1, "name": "Dave"}])

    @postgres_only
    def test_alter_column_unique(self):
        """
        Test altering a column uniqueness with MigrationManager.
        """
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
        asyncio.run(manager.run_backwards())
        self.run_sync(
            "INSERT INTO manager VALUES (default, 'Dave'), (default, 'Dave');"
        )
        response = self.run_sync("SELECT name FROM manager;")
        self.assertEqual(response, [{"name": "Dave"}, {"name": "Dave"}])

    @postgres_only
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
        asyncio.run(manager.run_backwards())
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

    @postgres_only
    def test_alter_column_digits(self):
        """
        Test altering a column digits with MigrationManager.
        """
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

        asyncio.run(manager.run_backwards())
        self.assertEqual(
            self._get_column_precision_and_scale(),
            [{"numeric_precision": 5, "numeric_scale": 2}],
        )

    @postgres_only
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

        asyncio.run(manager.run_backwards())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "''::character varying"}],
        )

    @postgres_only
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
        asyncio.run(manager_3.run_backwards())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

        asyncio.run(manager_2.run_backwards())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": "'Mr Manager'::character varying"}],
        )

        asyncio.run(manager_1.run_backwards())
        self.assertEqual(
            self._get_column_default(),
            [{"column_default": None}],
        )

    @postgres_only
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

        asyncio.run(manager.run_backwards())
        self.assertTrue(
            Manager._get_index_name(["name"])
            not in Manager.indexes().run_sync()
        )

    @postgres_only
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

        asyncio.run(manager.run_backwards())
        column_type_str = self.get_postgres_column_type(
            tablename="manager", column_name="name"
        )
        self.assertEqual(column_type_str, "CHARACTER VARYING")

    @postgres_only
    def test_alter_column_set_length(self):
        """
        Test altering a Varchar column's length with MigrationManager.
        """
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

        asyncio.run(manager.run_backwards())
        self.assertEqual(
            self.get_postgres_varchar_length(
                tablename="manager", column_name="name"
            ),
            200,
        )

    @postgres_only
    @patch.object(BaseMigrationManager, "get_migration_managers")
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
        set_mock_return_value(get_migration_managers, [manager_1])
        app_config = AppConfig(app_name="music", migrations_folder_path="")
        get_app_config.return_value = app_config
        asyncio.run(manager_2.run_backwards())

        get_migration_managers.assert_called_with(
            app_config=app_config, max_migration_id="2", offset=-1
        )
        self.assertTrue(self.table_exists("musician"))

        self.run_sync("DROP TABLE IF EXISTS musician;")
