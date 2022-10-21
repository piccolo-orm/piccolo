from unittest import TestCase

from piccolo.utils.warnings import colored_warning


class TestColoredWarning(TestCase):
    def test_colored_warning(self):
        """
        Just make sure no errors are raised.
        """
        colored_warning(message="TESTING!")
