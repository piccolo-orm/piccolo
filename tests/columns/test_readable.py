from piccolo import columns
from piccolo.columns.readable import Readable
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTable(Table):
    first_name = columns.Varchar()
    last_name = columns.Varchar()

    @classmethod
    def get_readable(cls) -> Readable:
        return Readable(
            template="%s %s", columns=[cls.first_name, cls.last_name]
        )


class TestReadable(TableTest):
    tables = [MyTable]

    def setUp(self):
        super().setUp()
        MyTable(first_name="Guido", last_name="van Rossum").save().run_sync()

    def test_readable(self):
        response = MyTable.select(MyTable.get_readable()).run_sync()
        self.assertEqual(response[0]["readable"], "Guido van Rossum")
