from unittest import TestCase

from piccolo.utils.printing import get_fixed_length_string


class TestGetFixedLengthString(TestCase):
    def test_extra_padding(self):
        """
        Make sure the additional padding is added.
        """
        result = get_fixed_length_string(string="hello", length=10)
        self.assertEqual(result, "hello     ")

    def test_truncation(self):
        """
        Make sure the string is truncated to the fixed length if it's too long.
        """
        result = get_fixed_length_string(
            string="this is a very, very long string", length=20
        )
        self.assertEqual(result, "this is a very, v...")
