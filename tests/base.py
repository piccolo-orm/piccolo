import asyncio
from unittest import TestCase

import pytest

from piccolo.engine.finder import engine_finder
from piccolo.engine.postgres import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine


ENGINE = engine_finder()


postgres_only = pytest.mark.skipif(
    not isinstance(ENGINE, PostgresEngine), reason="Only running for Postgres"
)


sqlite_only = pytest.mark.skipif(
    not isinstance(ENGINE, SQLiteEngine), reason="Only running for SQLite"
)


class DBTestCase(TestCase):
    """
    Using raw SQL, otherwise tests are too reliant on other Piccolo code.
    """

    def run_sync(self, query):
        asyncio.run(ENGINE._run_in_new_connection(query))

    def create_table(self):
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

    def drop_table(self):
        self.run_sync("DROP TABLE IF EXISTS band CASCADE;")
        self.run_sync("DROP TABLE IF EXISTS manager CASCADE;")

    def setUp(self):
        self.create_table()

    def tearDown(self):
        self.drop_table()
