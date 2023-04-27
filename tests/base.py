from __future__ import annotations

import asyncio
import sys
import typing as t
from unittest import TestCase
from unittest.mock import MagicMock

import pytest

from piccolo.apps.schema.commands.generate import RowMeta
from piccolo.engine.cockroach import CockroachEngine
from piccolo.engine.finder import engine_finder
from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table, create_table_class
from piccolo.utils.sync import run_sync

ENGINE = engine_finder()


def engine_version_lt(version: float):
    return ENGINE and run_sync(ENGINE.get_version()) < version


def is_running_postgres():
    return type(ENGINE) is PostgresEngine


def is_running_sqlite():
    return type(ENGINE) is SQLiteEngine


def is_running_cockroach():
    return type(ENGINE) is CockroachEngine


postgres_only = pytest.mark.skipif(
    not is_running_postgres(), reason="Only running for Postgres"
)

sqlite_only = pytest.mark.skipif(
    not is_running_sqlite(), reason="Only running for SQLite"
)

cockroach_only = pytest.mark.skipif(
    not is_running_cockroach(), reason="Only running for Cockroach"
)

unix_only = pytest.mark.skipif(
    sys.platform.startswith("win"), reason="Only running on a Unix system"
)


def engines_only(*engine_names: str):
    """
    Test decorator. Choose what engines can run a test.

    Example
        @engines_only('cockroach', 'postgres')
        def test_unknown_column_type(...):
            self.assertTrue(...)
    """
    if ENGINE:
        current_engine_name = ENGINE.engine_type
        if current_engine_name not in engine_names:

            def wrapper(func):
                return pytest.mark.skip(
                    f"Not running for {current_engine_name}"
                )(func)

            return wrapper
        else:

            def wrapper(func):
                return func

            return wrapper
    else:
        raise ValueError("Engine not found")


def engines_skip(*engine_names: str):
    """
    Test decorator. Choose what engines can run a test.

    Example
        @engines_skip('cockroach', 'postgres')
        def test_unknown_column_type(...):
            self.assertTrue(...)
    """
    if ENGINE:
        current_engine_name = ENGINE.engine_type
        if current_engine_name in engine_names:

            def wrapper(func):
                return pytest.mark.skip(
                    f"Not yet available for {current_engine_name}"
                )(func)

            return wrapper
        else:

            def wrapper(func):
                return func

            return wrapper
    else:
        raise ValueError("Engine not found")


def engine_is(*engine_names: str):
    """
    Assert branching. Choose what engines can run an assert.
    If branching becomes too complex, make a new test with
    @engines_only() or engines_skip()

    Example
        def test_unknown_column_type(...):
            if engine_is('cockroach', 'sqlite'):
                self.assertTrue(...)
    """
    if ENGINE:
        current_engine_name = ENGINE.engine_type
        if current_engine_name not in engine_names:
            return False
        else:
            return True
    else:
        raise ValueError("Engine not found")


class AsyncMock(MagicMock):
    """
    Async MagicMock for python 3.7+.

    This is a workaround for the fact that MagicMock is not async compatible in
    Python 3.7.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # this makes asyncio.iscoroutinefunction(AsyncMock()) return True
        self._is_coroutine = asyncio.coroutines._is_coroutine

    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class DBTestCase(TestCase):
    """
    Using raw SQL where possible, otherwise the tests are too reliant on other
    Piccolo code.
    """

    def run_sync(self, query):
        _Table = create_table_class(class_name="_Table")
        return _Table.raw(query).run_sync()

    def table_exists(self, tablename: str) -> bool:
        _Table: t.Type[Table] = create_table_class(
            class_name=tablename.upper(), class_kwargs={"tablename": tablename}
        )
        return _Table.table_exists().run_sync()

    ###########################################################################

    # Postgres specific utils

    def get_postgres_column_definition(
        self, tablename: str, column_name: str
    ) -> RowMeta:
        query = """
            SELECT {columns} FROM information_schema.columns
            WHERE table_name = '{tablename}'
            AND table_catalog = 'piccolo'
            AND column_name = '{column_name}'
        """.format(
            columns=RowMeta.get_column_name_str(),
            tablename=tablename,
            column_name=column_name,
        )
        response = self.run_sync(query)
        if len(response) > 0:
            return RowMeta(**response[0])
        else:
            raise ValueError("No such column")

    def get_postgres_column_type(
        self, tablename: str, column_name: str
    ) -> str:
        """
        Fetches the column type as a string, from the database.
        """
        return self.get_postgres_column_definition(
            tablename=tablename, column_name=column_name
        ).data_type.upper()

    def get_postgres_is_nullable(self, tablename, column_name: str) -> bool:
        """
        Fetches whether the column is defined as nullable, from the database.
        """
        return (
            self.get_postgres_column_definition(
                tablename=tablename, column_name=column_name
            ).is_nullable.upper()
            == "YES"
        )

    def get_postgres_varchar_length(
        self, tablename, column_name: str
    ) -> t.Optional[int]:
        """
        Fetches whether the column is defined as nullable, from the database.
        """
        return self.get_postgres_column_definition(
            tablename=tablename, column_name=column_name
        ).character_maximum_length

    ###########################################################################

    def create_tables(self):
        if ENGINE.engine_type in ("postgres", "cockroach"):
            self.run_sync(
                """
                CREATE TABLE manager (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50)
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE band (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE,
                    manager INTEGER REFERENCES manager,
                    popularity SMALLINT
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE ticket (
                    id SERIAL PRIMARY KEY,
                    price NUMERIC(5,2)
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE poster (
                    id SERIAL PRIMARY KEY,
                    content TEXT
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE shirt (
                    id SERIAL PRIMARY KEY,
                    size VARCHAR(1)
                );"""
            )
        elif ENGINE.engine_type == "sqlite":
            self.run_sync(
                """
                CREATE TABLE manager (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(50)
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE band (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(50),
                    manager INTEGER REFERENCES manager,
                    popularity SMALLINT
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE ticket (
                    id SERIAL PRIMARY KEY,
                    price NUMERIC(5,2)
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE poster (
                    id SERIAL PRIMARY KEY,
                    content TEXT
                );"""
            )
            self.run_sync(
                """
                CREATE TABLE shirt (
                    id SERIAL PRIMARY KEY,
                    size VARCHAR(1)
                );"""
            )
        else:
            raise Exception("Unrecognised engine")

    def insert_row(self):
        if ENGINE.engine_type == "cockroach":
            id = self.run_sync(
                """
                INSERT INTO manager (
                    name
                ) VALUES (
                    'Guido'
                ) RETURNING id;"""
            )
            self.run_sync(
                f"""
                INSERT INTO band (
                    name,
                    manager,
                    popularity
                ) VALUES (
                    'Pythonistas',
                    {id[0]["id"]},
                    1000
                );"""
            )
        else:
            self.run_sync(
                """
                INSERT INTO manager (
                    name
                ) VALUES (
                    'Guido'
                );"""
            )
            self.run_sync(
                """
                INSERT INTO band (
                    name,
                    manager,
                    popularity
                ) VALUES (
                    'Pythonistas',
                    1,
                    1000
                );"""
            )

    def insert_rows(self):
        if ENGINE.engine_type == "cockroach":
            id = self.run_sync(
                """
                INSERT INTO manager (
                    name
                ) VALUES (
                    'Guido'
                ),(
                    'Graydon'
                ),(
                    'Mads'
                ) RETURNING id;"""
            )
            self.run_sync(
                f"""
                INSERT INTO band (
                    name,
                    manager,
                    popularity
                ) VALUES (
                    'Pythonistas',
                    {id[0]["id"]},
                    1000
                ),(
                    'Rustaceans',
                    {id[1]["id"]},
                    2000
                ),(
                    'CSharps',
                    {id[2]["id"]},
                    10
                );"""
            )
        else:
            self.run_sync(
                """
                INSERT INTO manager (
                    name
                ) VALUES (
                    'Guido'
                ),(
                    'Graydon'
                ),(
                    'Mads'
                );"""
            )
            self.run_sync(
                """
                INSERT INTO band (
                    name,
                    manager,
                    popularity
                ) VALUES (
                    'Pythonistas',
                    1,
                    1000
                ),(
                    'Rustaceans',
                    2,
                    2000
                ),(
                    'CSharps',
                    3,
                    10
                );"""
            )

    def insert_many_rows(self, row_count=10000):
        """
        Insert lots of data - for testing retrieval of large numbers of rows.
        """
        values = ["('name_{}')".format(i) for i in range(row_count)]
        values_string = ",".join(values)
        self.run_sync(f"INSERT INTO manager (name) VALUES {values_string};")

    def drop_tables(self):
        if ENGINE.engine_type in ("postgres", "cockroach"):
            self.run_sync("DROP TABLE IF EXISTS band CASCADE;")
            self.run_sync("DROP TABLE IF EXISTS manager CASCADE;")
            self.run_sync("DROP TABLE IF EXISTS ticket CASCADE;")
            self.run_sync("DROP TABLE IF EXISTS poster CASCADE;")
            self.run_sync("DROP TABLE IF EXISTS shirt CASCADE;")
        elif ENGINE.engine_type == "sqlite":
            self.run_sync("DROP TABLE IF EXISTS band;")
            self.run_sync("DROP TABLE IF EXISTS manager;")
            self.run_sync("DROP TABLE IF EXISTS ticket;")
            self.run_sync("DROP TABLE IF EXISTS poster;")
            self.run_sync("DROP TABLE IF EXISTS shirt;")

    def setUp(self):
        self.create_tables()

    def tearDown(self):
        self.drop_tables()
