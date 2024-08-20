import datetime

from piccolo.columns.column_types import Date
from piccolo.columns.defaults.date import DateNow
from piccolo.table import Table
from piccolo.testing.test_case import TableTest


class MyTable(Table):
    created_on = Date()


class MyTableDefault(Table):
    created_on = Date(default=DateNow())


class TestDate(TableTest):
    tables = [MyTable]

    def test_timestamp(self):
        created_on = datetime.datetime.now().date()
        row = MyTable(created_on=created_on)
        row.save().run_sync()

        result = MyTable.objects().first().run_sync()
        assert result is not None
        self.assertEqual(result.created_on, created_on)


class TestDateDefault(TableTest):
    tables = [MyTableDefault]

    def test_timestamp(self):
        created_on = datetime.datetime.now().date()
        row = MyTableDefault()
        row.save().run_sync()

        result = MyTableDefault.objects().first().run_sync()
        assert result is not None
        self.assertEqual(result.created_on, created_on)
