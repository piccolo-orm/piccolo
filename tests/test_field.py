import unittest

from piccolo import columns


name_column = columns.Varchar()
# Usually this is handled by the Table MetaClass:
name_column.name = 'name'


class TestColumns(unittest.TestCase):

    def test_equals(self):
        _where = (name_column == 'Pythonistas')
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name = 'Pythonistas'")

    def test_not_equal(self):
        _where = (name_column != 'weedle')
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name != 'weedle'")

    def test_like(self):
        _where = name_column.like('Python%')
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name LIKE 'Python%'")

    def test_is_in(self):
        _where = name_column.is_in(['Pythonistas', 'raichu'])
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name IN ('Pythonistas', 'raichu')")

    def test_not_in(self):
        _where = name_column.not_in(['weedle'])
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name NOT IN ('weedle')")


class TestWhere():

    def test_and(self):
        """
        Need some high level tests ... Extend SQL to to include where
        clauses ...
        """
        pass
