from unittest import TestCase

from piccolo.utils.list import flatten


class TestFlatten(TestCase):
    def test_flatten(self):
        self.assertListEqual(flatten(["a", ["b", "c"]]), ["a", "b", "c"])
