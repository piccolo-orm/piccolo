import asyncio

from piccolo.migrations.auto import MigrationManager

from tests.base import DBTestCase


class TestMigrationManager(DBTestCase):
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

        with self.assertRaises(HasRun):
            asyncio.run(manager.run())

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

        with self.assertRaises(HasRun):
            asyncio.run(manager.run())
