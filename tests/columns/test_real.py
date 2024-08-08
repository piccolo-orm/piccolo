from piccolo.columns.column_types import Real
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTable(Table):
    column_a = Real()


class TestReal(TableTest):
    tables = [MyTable]

    def test_creation(self):
        row = MyTable(column_a=1.23)
        row.save().run_sync()

        _row = MyTable.objects().first().run_sync()
        assert _row is not None
        self.assertEqual(type(_row.column_a), float)
        self.assertAlmostEqual(_row.column_a, 1.23)
