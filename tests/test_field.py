import unittest

from piccolo import columns
from piccolo.table import Table


class MyTable(Table):
    name = columns.Varchar()


class TestColumns(unittest.TestCase):
    def test_equals(self):
        _where = MyTable.name == "Pythonistas"
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "my_table.name = 'Pythonistas'")

    def test_not_equal(self):
        _where = MyTable.name != "CSharps"
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "my_table.name != 'CSharps'")

    def test_like(self):
        _where = MyTable.name.like("Python%")
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "my_table.name LIKE 'Python%'")

    def test_is_in(self):
        _where = MyTable.name.is_in(["Pythonistas", "Rustaceans"])
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "my_table.name IN ('Pythonistas', 'Rustaceans')")

    def test_not_in(self):
        _where = MyTable.name.not_in(["CSharps"])
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "my_table.name NOT IN ('CSharps')")


class TestWhere:
    def test_and(self):
        """
        Need some high level tests ... Extend SQL to to include where
        clauses ...
        """
        pass
