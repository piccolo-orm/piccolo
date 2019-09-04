import asyncio
from unittest import TestCase

from piccolo.engine.finder import engine_finder


ENGINE = engine_finder()


class DBTestCase(TestCase):
    """
    Using raw SQL, otherwise tests are too reliant on other Piccolo code.
    """

    def run_sync(self, query):
        asyncio.run(ENGINE.run(query))

    def create_table(self):
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

    def drop_table(self):
        self.run_sync("DROP TABLE band;")
        self.run_sync("DROP TABLE manager;")

    def setUp(self):
        self.create_table()

    def tearDown(self):
        self.drop_table()
