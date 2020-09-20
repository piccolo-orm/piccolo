from unittest import TestCase

from piccolo.utils.printing import get_fixed_length_string


class TestGetFixedLengthString(TestCase):
    def test_get_fixed_length_string(self):
        result = get_fixed_length_string(string="hello", length=10)
        self.assertEqual(result, "hello     ")
