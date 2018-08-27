import unittest

from aragorm import fields


name_field = fields.Varchar()
# Usually this is handled by the Model MetaClass:
name_field.name = 'name'


class TestFields(unittest.TestCase):

    def test_equals(self):
        _where = (name_field == 'pikachu')
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name = 'pikachu'")

    def test_not_equal(self):
        _where = (name_field != 'weedle')
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name != 'weedle'")

    def test_like(self):
        _where = name_field.like('%chu')
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name LIKE '%chu'")

    def test_is_in(self):
        _where = name_field.is_in(['pikachu', 'raichu'])
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name IN ('pikachu', 'raichu')")

    def test_not_in(self):
        _where = name_field.not_in(['weedle'])
        sql = _where.__str__()
        print(sql)
        self.assertEqual(sql, "name NOT IN ('weedle')")


class TestWhere():

    def test_and(self):
        """
        Need some high level tests ... Extend SQL to to include where clauses ...
        """
        pass
