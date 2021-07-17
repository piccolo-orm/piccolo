from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.sql_shell.commands.run import run


class TestRun(TestCase):
    @patch("piccolo.apps.sql_shell.commands.run.subprocess")
    def test_run(self, subprocess: MagicMock):
        """
        A simple test to make sure it executes without raising any exceptions.
        """
        run()
        self.assertTrue(subprocess.run.called)
