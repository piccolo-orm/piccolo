from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.app.commands.show_all import show_all


class TestShowAll(TestCase):
    @patch("piccolo.apps.app.commands.show_all.print")
    def test_show_all(self, print_: MagicMock):
        show_all()

        self.assertEqual(
            print_.mock_calls,
            [
                call("Registered apps:"),
                call("tests.example_apps.music.piccolo_app"),
                call("tests.example_apps.mega.piccolo_app"),
            ],
        )
