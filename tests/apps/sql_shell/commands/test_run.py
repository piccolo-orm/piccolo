from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.sql_shell.commands.run import run
from tests.base import postgres_only, sqlite_only


class TestRun(TestCase):
    @postgres_only
    @patch("piccolo.apps.sql_shell.commands.run.subprocess")
    def test_psql(self, subprocess: MagicMock):
        """
        Make sure psql was called correctly.
        """
        run()
        self.assertTrue(subprocess.run.called)

        assert subprocess.run.call_args.args[0] == [
            "psql",
            "-U",
            "postgres",
            "-h",
            "localhost",
            "-p",
            "5432",
            "piccolo",
        ]

    @sqlite_only
    @patch("piccolo.apps.sql_shell.commands.run.subprocess")
    def test_sqlite3(self, subprocess: MagicMock):
        """
        Make sure sqlite3 was called correctly.
        """
        run()
        self.assertTrue(subprocess.run.called)

        assert subprocess.run.call_args.args[0] == ["sqlite3", "test.sqlite"]
