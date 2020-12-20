import unittest

from ..example_app.tables import Band


class TestWhere(unittest.TestCase):
    def test_equals(self):
        _where = Band.name == "Pythonistas"
        sql = _where.__str__()
        self.assertEqual(sql, "band.name = 'Pythonistas'")

    def test_not_equal(self):
        _where = Band.name != "CSharps"
        sql = _where.__str__()
        self.assertEqual(sql, "band.name != 'CSharps'")

    def test_like(self):
        _where = Band.name.like("Python%")
        sql = _where.__str__()
        self.assertEqual(sql, "band.name LIKE 'Python%'")

    def test_is_in(self):
        _where = Band.name.is_in(["Pythonistas", "Rustaceans"])
        sql = _where.__str__()
        self.assertEqual(sql, "band.name IN ('Pythonistas', 'Rustaceans')")

        with self.assertRaises(ValueError):
            Band.name.is_in([])

    def test_not_in(self):
        _where = Band.name.not_in(["CSharps"])
        sql = _where.__str__()
        self.assertEqual(sql, "band.name NOT IN ('CSharps')")

        with self.assertRaises(ValueError):
            Band.name.not_in([])
