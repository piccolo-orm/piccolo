from unittest import TestCase

from piccolo.apps.playground.commands.run import Genre, Manager


class TestTableStr(TestCase):
    def test_all_attributes(self):
        self.assertEqual(
            Manager._table_str(),
            (
                "class Manager(Table, tablename='manager'):\n"
                "    id = Serial(null=False, primary_key=True, unique=False, index=False, index_method=IndexMethod.btree, choices=None, db_column_name='id', secret=False)\n"  # noqa: E501
                "    name = Varchar(length=50, default='', null=False, primary_key=False, unique=False, index=False, index_method=IndexMethod.btree, choices=None, db_column_name=None, secret=False)\n"  # noqa: E501
            ),
        )

    def test_abbreviated(self):
        self.assertEqual(
            Manager._table_str(abbreviated=True),
            (
                "class Manager(Table):\n"
                "    id = Serial(primary_key=True)\n"
                "    name = Varchar(length=50)\n"
            ),
        )

    def test_m2m(self):
        """
        Make sure M2M relationships appear in the Table string.
        """

        self.assertEqual(
            Genre._table_str(abbreviated=True),
            (
                "class Genre(Table):\n"
                "    id = Serial(primary_key=True)\n"
                "    name = Varchar()\n"
                "    bands = M2M(GenreToBand)\n"
            ),
        )

    def test_print(self):
        """
        Make sure we can print it directly without any errors.
        """
        print(Manager)
