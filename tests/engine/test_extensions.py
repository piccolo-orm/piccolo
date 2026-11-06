import asyncio
from typing import cast
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from piccolo.columns.column_types import Varchar, Vector
from piccolo.columns.indexes import IndexMethod
from piccolo.engine import extensions
from piccolo.engine.exceptions import ExtensionNotInstalled
from piccolo.engine.extensions import (
    _assert_extensions_installed,
    register_codecs,
)
from piccolo.engine.postgres import PostgresEngine
from piccolo.query.methods.create_index import CreateIndex
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_only, pgvector_installed, postgres_only


class ItemTable(Table):
    embedding = Vector(dimensions=3)
    name = Varchar()


def _make_connection(schema=None) -> MagicMock:
    connection = MagicMock()
    connection.fetchval = AsyncMock(return_value=schema)
    connection.set_type_codec = AsyncMock()
    return connection


class TestRegisterCodecs(IsolatedAsyncioTestCase):

    async def test_uses_extension_schema(self) -> None:
        """
        Make sure the codec is registered in whichever schema the extension
        is installed in, rather than assuming ``public``.
        """
        connection = _make_connection(schema="extensions")
        cache: dict[str, str] = {}

        await register_codecs(connection, cache)

        self.assertEqual(
            connection.set_type_codec.call_args.kwargs["schema"],
            "extensions",
        )
        self.assertEqual(cache, {"vector": "extensions"})

    async def test_schema_is_cached(self) -> None:
        """
        Make sure the schema is only looked up once per engine.
        """
        cache: dict[str, str] = {}
        await register_codecs(_make_connection(schema="public"), cache)

        connection = _make_connection(schema="public")
        await register_codecs(connection, cache)

        connection.fetchval.assert_not_called()
        connection.set_type_codec.assert_awaited_once()

    async def test_missing_extension_not_cached(self) -> None:
        """
        If the extension isn't installed, do nothing, and don't cache the
        result - so an extension created later is picked up by new
        connections.
        """
        cache: dict[str, str] = {}
        connection = _make_connection(schema=None)

        await register_codecs(connection, cache)

        connection.set_type_codec.assert_not_called()
        self.assertEqual(cache, {})

        connection = _make_connection(schema="public")
        await register_codecs(connection, cache)
        connection.set_type_codec.assert_awaited_once()

    async def test_dropped_extension_clears_cache(self) -> None:
        """
        If the extension was dropped since we cached the schema, don't raise
        an error, and look it up again next time.
        """
        cache = {"vector": "public"}
        connection = _make_connection()
        connection.set_type_codec.side_effect = ValueError(
            "unknown type: public.vector"
        )

        await register_codecs(connection, cache)

        self.assertEqual(cache, {})

    async def test_skipped_if_no_columns_need_it(self) -> None:
        """
        If no column needs a codec, there should be no extra queries.
        """
        connection = _make_connection(schema="public")

        with patch.object(extensions, "_used_extensions", set()):
            await register_codecs(connection, {})

        connection.fetchval.assert_not_called()
        connection.set_type_codec.assert_not_called()


@engines_only("postgres")
class TestAssertExtensionsInstalled(IsolatedAsyncioTestCase):

    async def test_single_query(self) -> None:
        """
        Make sure all of the extensions are checked using a single query.
        """
        engine = cast(PostgresEngine, ItemTable._meta.db)
        with patch.object(
            PostgresEngine,
            "run_querystring",
            AsyncMock(return_value=[{"extname": "pg_trgm"}]),
        ) as run_querystring:
            with self.assertRaises(ExtensionNotInstalled) as manager:
                await _assert_extensions_installed(
                    engine, {"vector", "pg_trgm"}
                )

        run_querystring.assert_awaited_once()
        self.assertIn("'vector'", str(manager.exception))
        self.assertNotIn("'pg_trgm'", str(manager.exception))

    async def test_nothing_needed(self) -> None:
        """
        If no extensions are needed, there shouldn't be a query.
        """
        engine = cast(PostgresEngine, ItemTable._meta.db)
        with patch.object(
            PostgresEngine, "run_querystring", AsyncMock()
        ) as run_querystring:
            await _assert_extensions_installed(engine, set())

        run_querystring.assert_not_called()


@engines_only("postgres")
class TestExtensionCheckInPool(TestCase):
    """
    The extension check has to respect ``in_pool``, otherwise ``run_sync``
    can borrow a pool connection which belongs to another event loop.
    """

    def _run(self, query) -> AsyncMock:
        with patch.object(
            PostgresEngine,
            "run_querystring",
            AsyncMock(return_value=[{"extname": "vector"}]),
        ) as run_querystring, patch.object(
            PostgresEngine, "run_ddl", AsyncMock()
        ):
            query.run_sync()
        return run_querystring

    def test_create(self):
        run_querystring = self._run(ItemTable.create_table())
        self.assertIs(run_querystring.call_args.kwargs["in_pool"], False)

    def test_create_index(self):
        run_querystring = self._run(
            CreateIndex(
                ItemTable, [ItemTable.embedding], method=IndexMethod.hnsw
            )
        )
        self.assertIs(run_querystring.call_args.kwargs["in_pool"], False)

    def test_create_with_pool_from_another_loop(self):
        """
        A pool created in one event loop, then ``create_table().run_sync()``
        in another.
        """
        engine = cast(PostgresEngine, ItemTable._meta.db)
        pool_loop = asyncio.new_event_loop()
        pool_loop.run_until_complete(engine.start_connection_pool())
        try:
            with patch.object(PostgresEngine, "run_ddl", AsyncMock()):
                # `run_sync` uses a new event loop.
                ItemTable.create_table(if_not_exists=True).run_sync()
        finally:
            pool_loop.run_until_complete(engine.close_connection_pool())
            pool_loop.close()


@postgres_only
@pgvector_installed
class TestPoolInit(TableTest):
    tables = [ItemTable]

    def test_user_init_is_chained(self):
        """
        Make sure the user can pass their own ``init`` hook to the pool, and
        that the pgvector codec is still registered.
        """
        engine = cast(PostgresEngine, ItemTable._meta.db)
        user_init = AsyncMock()

        async def run():
            await engine.start_connection_pool(
                init=user_init, min_size=1, max_size=1
            )
            try:
                await ItemTable({ItemTable.embedding: [1.0, 2.0, 3.0]}).save()
                return await ItemTable.select(ItemTable.embedding)
            finally:
                await engine.close_connection_pool()

        response = asyncio.run(run())

        user_init.assert_awaited()
        self.assertEqual(response, [{"embedding": [1.0, 2.0, 3.0]}])
