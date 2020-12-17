from unittest import TestCase
from unittest.mock import call, patch

from piccolo.apps.app.commands.show_all import show_all


class TestShowAll(TestCase):
    @patch("piccolo.apps.app.commands.show_all.print")
    def test_show_all(self, mocked_print):
        show_all()

        self.assertEqual(
            mocked_print.mock_calls,
            [call("Registered apps:"), call("tests.example_app.piccolo_app")],
        )
