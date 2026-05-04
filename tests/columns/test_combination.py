import unittest

from tests.example_apps.music.tables import Band, Concert


class TestWhere(unittest.TestCase):
    def test_equals(self):
        _where = Band.name == "Pythonistas"
        sql = _where.__str__()
        self.assertEqual(sql, '"band"."name" = \'Pythonistas\'')

    def test_not_equal(self):
        _where = Band.name != "CSharps"
        sql = _where.__str__()
        self.assertEqual(sql, '"band"."name" != \'CSharps\'')

    def test_like(self):
        _where = Band.name.like("Python%")
        sql = _where.__str__()
        self.assertEqual(sql, '"band"."name" LIKE \'Python%\'')

    def test_is_in(self):
        _where = Band.name.is_in(["Pythonistas", "Rustaceans"])
        sql = _where.__str__()
        self.assertEqual(
            sql, "\"band\".\"name\" IN ('Pythonistas', 'Rustaceans')"
        )

        with self.assertRaises(ValueError):
            Band.name.is_in([])

    def test_is_in_subquery(self):
        _where = Band.id.is_in(
            Concert.select(Concert.band_1).where(Concert.band_1 == 1)
        )
        sql = _where.__str__()
        self.assertEqual(
            sql,
            '"band"."id" IN (SELECT ALL "concert"."band_1" AS "band_1" FROM "concert" WHERE "concert"."band_1" = 1)',  # noqa: E501
        )

        # a sub select must only return a single column
        with self.assertRaises(ValueError):
            Band.id.is_in(Concert.select().where(Concert.band_1 == 1))

    def test_not_in(self):
        _where = Band.name.not_in(["CSharps"])
        sql = _where.__str__()
        self.assertEqual(sql, '"band"."name" NOT IN (\'CSharps\')')

        with self.assertRaises(ValueError):
            Band.name.not_in([])

    def test_not_in_subquery(self):
        _where = Band.id.not_in(
            Concert.select(Concert.band_1).where(Concert.band_1 == 1)
        )
        sql = _where.__str__()
        self.assertEqual(
            sql,
            '"band"."id" NOT IN (SELECT ALL "concert"."band_1" AS "band_1" FROM "concert" WHERE "concert"."band_1" = 1)',  # noqa: E501
        )

        # a sub select must only return a single column
        with self.assertRaises(ValueError):
            Band.id.not_in(Concert.select().where(Concert.band_1 == 1))


class TestAnd(unittest.TestCase):
    def test_get_column_values(self):
        """
        Make sure that we can extract the column values from an ``And``.

        There was a bug with ``None`` values not working:

        https://github.com/piccolo-orm/piccolo/issues/715

        """
        And_ = (Band.manager.is_null()) & (Band.name == "Pythonistas")
        column_values = And_.get_column_values()

        self.assertDictEqual(
            column_values, {Band.name: "Pythonistas", Band.manager: None}
        )
