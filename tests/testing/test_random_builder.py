import unittest
from enum import Enum

from piccolo.testing.random_builder import RandomBuilder


class TestRandomBuilder(unittest.TestCase):
    def test_next_bool(self):
        random_bool = RandomBuilder.next_bool()
        self.assertIn(random_bool, [True, False])

    def test_next_bytes(self):
        random_bytes = RandomBuilder.next_bytes(length=100)
        self.assertEqual(len(random_bytes), 100)

    def test_next_date(self):
        random_date = RandomBuilder.next_date()
        self.assertGreaterEqual(random_date.year, 2000)
        self.assertLessEqual(random_date.year, 2050)

    def test_next_datetime(self):
        random_datetime = RandomBuilder.next_datetime()
        self.assertGreaterEqual(random_datetime.year, 2000)
        self.assertLessEqual(random_datetime.year, 2050)

    def test_next_enum(self):
        class Color(Enum):
            RED = 1
            BLUE = 2

        random_enum = RandomBuilder.next_enum(Color)
        self.assertIsInstance(random_enum, int)

    def test_next_float(self):
        random_float = RandomBuilder.next_float(maximum=1000)
        self.assertLessEqual(random_float, 1000)

    def test_next_int(self):
        random_int = RandomBuilder.next_int()
        self.assertLessEqual(random_int, 2147483647)

    def test_next_str(self):
        random_str = RandomBuilder.next_str(length=64)
        self.assertLessEqual(len(random_str), 64)

    def test_next_time(self):
        RandomBuilder.next_time()

    def test_next_timedelta(self):
        random_timedelta = RandomBuilder.next_timedelta()
        self.assertLessEqual(random_timedelta.days, 7)

    def test_next_uuid(self):
        RandomBuilder.next_uuid()
