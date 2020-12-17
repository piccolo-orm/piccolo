from unittest import TestCase

from ..example_app.tables import Manager


class TestTableStr(TestCase):
    def test_str(self):
        self.assertEqual(
            Manager._table_str(),
            (
                "class Manager(Table, tablename='manager'):\n"
                "    id = PrimaryKey(null=False, primary=True, key=True, unique=False, index=False)\n"  # noqa
                "    name = Varchar(length=50, default='', null=False, primary=False, key=False, unique=False, index=False)\n"  # noqa
            ),
        )

        self.assertEqual(
            Manager._table_str(abbreviated=True),
            (
                "class Manager(Table):\n"
                "    id = PrimaryKey()\n"
                "    name = Varchar()\n"
            ),
        )

        # We should also be able to print it directly.
        print(Manager)
