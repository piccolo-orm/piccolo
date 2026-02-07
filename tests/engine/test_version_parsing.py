from unittest import TestCase

from piccolo.engine.mysql import MySQLEngine
from piccolo.engine.postgres import PostgresEngine

from ..base import engines_only


@engines_only("postgres", "cockroach")
class TestVersionParsing(TestCase):
    def test_version_parsing(self):
        """
        Make sure the version number can correctly be parsed from a range
        of known formats.
        """
        self.assertEqual(
            PostgresEngine._parse_raw_version_string(version_string="9.4"), 9.4
        )

        self.assertEqual(
            PostgresEngine._parse_raw_version_string(version_string="9.4.1"),
            9.4,
        )

        self.assertEqual(
            PostgresEngine._parse_raw_version_string(
                version_string="12.4 (Ubuntu 12.4-0ubuntu0.20.04.1)"
            ),
            12.4,
        )


@engines_only("mysql")
class TestVersionParsingMySQL(TestCase):
    def test_version_parsing(self):
        """
        Make sure the version number can correctly be parsed from a range
        of known formats.
        """
        self.assertEqual(
            MySQLEngine._parse_raw_version_string(version_string="8.0"), 8.0
        )

        self.assertEqual(
            MySQLEngine._parse_raw_version_string(version_string="8.4.7"),
            8.4,
        )

        self.assertEqual(
            MySQLEngine._parse_raw_version_string(
                version_string="8.4.7 MySQL Community Server"
            ),
            8.4,
        )
