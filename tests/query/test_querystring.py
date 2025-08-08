from unittest import TestCase

from piccolo.querystring import QueryString
from tests.base import postgres_only


# TODO - add more extensive tests (increased nesting and argument count).
class TestQueryString(TestCase):

    qs = QueryString(
        "SELECT id FROM band {}", QueryString("WHERE name = {}", "Pythonistas")
    )

    def test_compile_string(self):
        compiled_string, args = self.qs.compile_string()

        self.assertEqual(
            compiled_string, "SELECT id FROM band WHERE name = $1"
        )

        self.assertEqual(args, ["Pythonistas"])

    def test_string(self):
        string = self.qs.__str__()
        self.assertEqual(
            string, "SELECT id FROM band WHERE name = 'Pythonistas'"
        )

    def test_querystring_with_no_args(self):
        qs = QueryString("SELECT name FROM band")
        self.assertEqual(qs.compile_string(), ("SELECT name FROM band", []))


@postgres_only
class TestQueryStringOperators(TestCase):
    """
    Make sure basic operations can be used on ``QueryString``.
    """

    def test_add(self):
        query = QueryString("SELECT price") + 1
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price + $1", [1]),
        )

    def test_multiply(self):
        query = QueryString("SELECT price") * 2
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price * $1", [2]),
        )

    def test_divide(self):
        query = QueryString("SELECT price") / 1
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price / $1", [1]),
        )

    def test_power(self):
        query = QueryString("SELECT price") ** 2
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price ^ $1", [2]),
        )

    def test_subtract(self):
        query = QueryString("SELECT price") - 1
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price - $1", [1]),
        )

    def test_modulus(self):
        query = QueryString("SELECT price") % 1
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price % $1", [1]),
        )

    def test_like(self):
        query = QueryString("strip(name)").like("Python%")
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("strip(name) LIKE $1", ["Python%"]),
        )

    def test_ilike(self):
        query = QueryString("strip(name)").ilike("Python%")
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("strip(name) ILIKE $1", ["Python%"]),
        )

    def test_greater_than(self):
        query = QueryString("SELECT price") > 10
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price > $1", [10]),
        )

    def test_greater_equal_than(self):
        query = QueryString("SELECT price") >= 10
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price >= $1", [10]),
        )

    def test_less_than(self):
        query = QueryString("SELECT price") < 10
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price < $1", [10]),
        )

    def test_less_equal_than(self):
        query = QueryString("SELECT price") <= 10
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price <= $1", [10]),
        )

    def test_equals(self):
        query = QueryString("SELECT price") == 10
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price = $1", [10]),
        )

    def test_not_equals(self):
        query = QueryString("SELECT price") != 10
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price != $1", [10]),
        )

    def test_is_in(self):
        query = QueryString("SELECT price").is_in([10, 20, 30])
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price IN $1", [[10, 20, 30]]),
        )

    def test_not_in(self):
        query = QueryString("SELECT price").not_in([10, 20, 30])
        self.assertIsInstance(query, QueryString)
        self.assertEqual(
            query.compile_string(),
            ("SELECT price NOT IN $1", [[10, 20, 30]]),
        )
