import asyncio
import os
import tempfile
from unittest import TestCase
from unittest.mock import call, patch

from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
from tests.base import DBTestCase, engine_is, engines_only, sqlite_only
from tests.example_apps.music.tables import Manager


@engines_only("postgres", "cockroach")
class TestPool(DBTestCase):
    async def _create_pool(self):
        engine: PostgresEngine = Manager._meta.db

        await engine.start_connection_pool()
        assert engine.pool is not None

        await engine.close_connection_pool()
        assert engine.pool is None

    async def _make_query(self):
        await Manager._meta.db.start_connection_pool()

        await Manager(name="Bob").save().run()
        response = await Manager.select().run()
        self.assertIn("Bob", [i["name"] for i in response])

        await Manager._meta.db.close_connection_pool()

    async def _make_many_queries(self):
        await Manager._meta.db.start_connection_pool()

        await Manager(name="Bob").save().run()

        async def get_data():
            response = await Manager.select().run()
            if engine_is("cockroach"):
                self.assertEqual(
                    response, [{"id": response[0]["id"], "name": "Bob"}]
                )
            else:
                self.assertEqual(response, [{"id": 1, "name": "Bob"}])

        await asyncio.gather(*[get_data() for _ in range(500)])

        await Manager._meta.db.close_connection_pool()

    def test_creation(self):
        """
        Make sure a connection pool can be created.
        """
        asyncio.run(self._create_pool())

    def test_query(self):
        """
        Make several queries using a connection pool.
        """
        asyncio.run(self._make_query())

    def test_many_queries(self):
        """
        Make sure the connection pool is working correctly, and we don't
        exceed a connection limit - queries should queue, then succeed.
        """
        asyncio.run(self._make_many_queries())


@engines_only("postgres", "cockroach")
class TestPoolProxyMethods(DBTestCase):
    async def _create_pool(self):
        engine: PostgresEngine = Manager._meta.db

        # Deliberate typo ('nnn'):
        await engine.start_connnection_pool()
        assert engine.pool is not None

        # Deliberate typo ('nnn'):
        await engine.close_connnection_pool()
        assert engine.pool is None

    def test_proxy_methods(self):
        """
        There are some proxy methods, due to some old typos. Make sure they
        work, to ensure backwards compatibility.
        """
        asyncio.run(self._create_pool())


@sqlite_only
class TestConnectionPoolWarning(TestCase):
    async def _create_pool(self):
        sqlite_file = os.path.join(tempfile.gettempdir(), "engine.sqlite")
        engine = SQLiteEngine(path=sqlite_file)

        with patch("piccolo.engine.base.colored_warning") as colored_warning:
            await engine.start_connection_pool()
            await engine.close_connection_pool()

            self.assertEqual(
                colored_warning.call_args_list,
                [
                    call(
                        "Connection pooling is not supported for sqlite.",
                        stacklevel=3,
                    ),
                    call(
                        "Connection pooling is not supported for sqlite.",
                        stacklevel=3,
                    ),
                ],
            )

    def test_warnings(self):
        """
        Make sure that when trying to start and close a connection pool with
        SQLite, a warning is printed out, as connection pools aren't currently
        supported.
        """
        asyncio.run(self._create_pool())
