import string
from unittest import TestCase

from piccolo.utils.list import batch, flatten


class TestFlatten(TestCase):
    def test_flatten(self):
        self.assertListEqual(flatten(["a", ["b", "c"]]), ["a", "b", "c"])


class TestBatch(TestCase):
    def test_batch(self):
        self.assertListEqual(
            batch([i for i in string.ascii_lowercase], chunk_size=5),
            [
                ["a", "b", "c", "d", "e"],
                ["f", "g", "h", "i", "j"],
                ["k", "l", "m", "n", "o"],
                ["p", "q", "r", "s", "t"],
                ["u", "v", "w", "x", "y"],
                ["z"],
            ],
        )

    def test_zero(self):
        with self.assertRaises(ValueError):
            batch([1, 2, 3], chunk_size=0)
