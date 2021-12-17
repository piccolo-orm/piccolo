from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.meta.commands.version import version


class TestVersion(TestCase):
    @patch("piccolo.apps.meta.commands.version.print")
    def test_version(self, print_: MagicMock):
        version()
        print_.assert_called_once()
