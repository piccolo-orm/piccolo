from unittest import TestCase

from piccolo.engine.postgres import PostgresEngine

from ..base import postgres_only


@postgres_only
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
