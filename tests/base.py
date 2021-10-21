from __future__ import annotations

import typing as t
from unittest import TestCase
from unittest.mock import MagicMock

import pytest

from piccolo.apps.schema.commands.generate import RowMeta
from piccolo.engine.finder import engine_finder
from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table, create_table_class

ENGINE = engine_finder()


postgres_only = pytest.mark.skipif(
    not isinstance(ENGINE, PostgresEngine), reason="Only running for Postgres"
)


sqlite_only = pytest.mark.skipif(
    not isinstance(ENGINE, SQLiteEngine), reason="Only running for SQLite"
)


def set_mock_return_value(magic_mock: MagicMock, return_value: t.Any):
    """
    Python 3.8 has good support for mocking coroutines. For older versions,
    we must set the return value to be an awaitable explicitly.
    """
    if magic_mock.__class__.__name__ == "AsyncMock":
        # Python 3.8 and above
        magic_mock.return_value = return_value
    else:

        async def coroutine(*args, **kwargs):
            return return_value

        magic_mock.return_value = coroutine()


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
        if ENGINE.engine_type == "postgres":
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
        if ENGINE.engine_type == "postgres":
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
