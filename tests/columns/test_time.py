import datetime
from functools import partial

from piccolo.columns.column_types import Time
from piccolo.columns.defaults.time import TimeNow
from piccolo.table import Table
from piccolo.testing.test_case import TableTest
from tests.base import engines_skip


class MyTable(Table):
    created_on = Time()


class MyTableDefault(Table):
    created_on = Time(default=TimeNow())


class TestTime(TableTest):
    tables = [MyTable]

    @engines_skip("cockroach")
    def test_timestamp(self):
        created_on = datetime.datetime.now().time()
        row = MyTable(created_on=created_on)
        row.save().run_sync()

        result = MyTable.objects().first().run_sync()
        assert result is not None
        self.assertEqual(result.created_on, created_on)


class TestTimeDefault(TableTest):
    tables = [MyTableDefault]

    @engines_skip("cockroach")
    def test_timestamp(self):
        created_on = datetime.datetime.now().time()
        row = MyTableDefault()
        row.save().run_sync()

        _datetime = partial(datetime.datetime, year=2020, month=1, day=1)

        result = MyTableDefault.objects().first().run_sync()
        assert result is not None
        self.assertLess(
            _datetime(
                hour=result.created_on.hour,
                minute=result.created_on.minute,
                second=result.created_on.second,
            )
            - _datetime(
                hour=created_on.hour,
                minute=created_on.minute,
                second=created_on.second,
            ),
            datetime.timedelta(seconds=1),
        )
