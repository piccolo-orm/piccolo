from unittest import TestCase, mock

import aiosqlite
import asyncpg  # type: ignore

from piccolo.utils.lazy_loader import LazyLoader


class TestLazyLoader(TestCase):
    def test_lazy_loading_database_driver(self):
        _ = LazyLoader("asyncpg", globals(), "asyncpg")

    def test_lazy_loader_asyncpg_exception(self):
        lazy_loader = LazyLoader("asyncpg", globals(), "asyncpg.connect")

        with mock.patch.object(asyncpg, "connect") as module:
            module.side_effect = ModuleNotFoundError()
            with self.assertRaises(ModuleNotFoundError):
                lazy_loader._load()

    def test_lazy_loader_aiosqlite_exception(self):
        lazy_loader = LazyLoader("aiosqlite", globals(), "aiosqlite.connect")

        with mock.patch.object(aiosqlite, "connect") as module:
            module.side_effect = ModuleNotFoundError()
            with self.assertRaises(ModuleNotFoundError):
                lazy_loader._load()
