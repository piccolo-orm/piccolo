import asyncio
from unittest import TestCase

from piccolo.columns.column_types import Varchar
from piccolo.engine.exceptions import TransactionError
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table
from tests.base import DBTestCase, sqlite_only
from tests.example_apps.music.tables import Manager

ENGINE_1 = SQLiteEngine(path="engine1.sqlite")
ENGINE_2 = SQLiteEngine(path="engine2.sqlite")


class Musician(Table, db=ENGINE_1):
    name = Varchar(length=100)


class Roadie(Table, db=ENGINE_2):
    name = Varchar(length=100)


@sqlite_only
class TestDifferentDB(TestCase):
    def setUp(self):
        ENGINE_1.remove_db_file()
        ENGINE_2.remove_db_file()

    def tearDown(self):
        ENGINE_1.remove_db_file()
        ENGINE_2.remove_db_file()

    async def run_nested(self):
        """
        Make sure nested transactions which reference different databases work
        as expected.
        """
        async with Musician._meta.db.transaction():
            await Musician.create_table().run()
            await Musician(name="Bob").save().run()

            async with Roadie._meta.db.transaction():
                await Roadie.create_table().run()
                await Roadie(name="Dave").save().run()

        self.assertTrue(await Musician.table_exists().run())
        musician = await Musician.select("name").first().run()
        self.assertEqual(musician["name"], "Bob")

        self.assertTrue(await Roadie.table_exists().run())
        roadie = await Roadie.select("name").first().run()
        self.assertEqual(roadie["name"], "Dave")

    def test_nested(self):
        asyncio.run(self.run_nested())


class TestSameDB(DBTestCase):
    async def run_nested(self):
        """
        Nested transactions currently aren't permitted in a connection.
        """
        # allow_nested=False
        with self.assertRaises(TransactionError):
            async with Manager._meta.db.transaction():
                await Manager(name="Bob").save().run()

                async with Manager._meta.db.transaction(allow_nested=False):
                    pass

        # allow_nested=True
        async with Manager._meta.db.transaction():
            async with Manager._meta.db.transaction():
                # Shouldn't raise an exception
                pass

        # Utilise returned transaction.
        async with Manager._meta.db.transaction():
            async with Manager._meta.db.transaction() as transaction:
                await Manager(name="Dave").save().run()
                await transaction.rollback()

    def test_nested(self):
        asyncio.run(self.run_nested())
