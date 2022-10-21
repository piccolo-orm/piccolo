from unittest import TestCase

from piccolo.querystring import QueryString


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
