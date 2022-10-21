from unittest import TestCase

from piccolo.utils.encoding import dump_json, load_json


class TestEncodingDecoding(TestCase):
    def test_dump_load(self):
        """
        Test dumping then loading an object.
        """
        payload = {"a": [1, 2, 3]}
        self.assertEqual(load_json(dump_json(payload)), payload)
