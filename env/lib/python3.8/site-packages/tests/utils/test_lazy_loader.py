from unittest import TestCase, mock

from piccolo.utils.lazy_loader import LazyLoader
from tests.base import engines_only, sqlite_only


class TestLazyLoader(TestCase):
    def test_lazy_loading_database_driver(self):
        _ = LazyLoader("asyncpg", globals(), "asyncpg")

    @engines_only("postgres", "cockroach")
    def test_lazy_loader_asyncpg_exception(self):
        lazy_loader = LazyLoader("asyncpg", globals(), "asyncpg.connect")

        with mock.patch("asyncpg.connect") as module:
            module.side_effect = ModuleNotFoundError()
            with self.assertRaises(ModuleNotFoundError):
                lazy_loader._load()

    @sqlite_only
    def test_lazy_loader_aiosqlite_exception(self):
        lazy_loader = LazyLoader("aiosqlite", globals(), "aiosqlite.connect")

        with mock.patch("aiosqlite.connect") as module:
            module.side_effect = ModuleNotFoundError()
            with self.assertRaises(ModuleNotFoundError):
                lazy_loader._load()
