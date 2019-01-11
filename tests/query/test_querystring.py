from unittest import TestCase

from piccolo.query.querystring import QueryString

from ..example_project.tables import Band


class TestQuerystring(TestCase):

    # This is kind of an artificial example - you wouldn't use parameters
    # for table names and columns.
    qs = QueryString(
        'SELECT {} FROM {} {}',
        QueryString(
            '{}, {}',
            'id',
            'name'
        ),
        'band',
        QueryString(
            "WHERE {} = '{}'",
            'name',
            'Pythonistas'
        )
    )

    def test_compile_string(self):
        compiled_string, args = self.qs.compile_string()

        self.assertEqual(
            compiled_string,
            "SELECT $1, $2 FROM $3 WHERE $4 = '$5'"
        )

        self.assertEqual(
            args,
            ['id', 'name', 'band', 'name', 'Pythonistas']
        )

    def test_string(self):
        string = self.qs.__str__()
        self.assertEqual(
            string,
            "SELECT id, name FROM band WHERE name = 'Pythonistas'"
        )


# class TestExecuteQuerystring(TestCase):

#     def setUp():
#         Band.create.run_sync()

#     def tearDown():
#         Band.drop.run_sync()

#     def test_raw_query(self):
#         Band.Meta.db.run()
