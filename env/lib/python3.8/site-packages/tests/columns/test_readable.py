import unittest

from piccolo import columns
from piccolo.columns.readable import Readable
from piccolo.table import Table


class MyTable(Table):
    first_name = columns.Varchar()
    last_name = columns.Varchar()

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s %s", columns=[cls.first_name, cls.last_name]
        )


class TestReadable(unittest.TestCase):
    def setUp(self):
        MyTable.create_table().run_sync()
        MyTable(first_name="Guido", last_name="van Rossum").save().run_sync()

    def test_readable(self):
        response = MyTable.select(MyTable.get_readable()).run_sync()
        self.assertEqual(response[0]["readable"], "Guido van Rossum")

    def tearDown(self):
        MyTable.alter().drop_table().run_sync()
