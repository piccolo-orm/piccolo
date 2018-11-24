from ..base import DBTestCase
from ..example_project.tables import Band


class TestSelect(DBTestCase):

    def test_query_all_columns(self):
        self.insert_row()

        response = Band.select().run_sync()
        print(f'response = {response}')

        self.assertDictEqual(
            response[0],
            {'id': 1, 'name': 'pikachu', 'trainer': 'ash', 'power': 1000}
        )

    def test_query_some_columns(self):
        self.insert_row()

        response = Band.select('name').run_sync()
        print(f'response = {response}')

        self.assertDictEqual(
            response[0],
            {'name': 'pikachu'}
        )

    def test_where_like(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            Band.name.like('%chu')
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}, {'name': 'raichu'}]
        )

    def test_where_greater_than(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            Band.power > 1000
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}]
        )

    def test_where_greater_equal_than(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            Band.power >= 1000
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}, {'name': 'raichu'}]
        )

    def test_where_less_than(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            Band.power < 1000
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'weedle'}]
        )

    def test_where_less_equal_than(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            Band.power <= 1000
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}, {'name': 'weedle'}]
        )

    def test_where_and(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            (Band.power <= 1000) & (Band.name.like('%chu'))
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}]
        )

    def test_where_or(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            (Band.name == 'raichu') | (Band.name == 'weedle')
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}, {'name': 'weedle'}]
        )

    def test_multiple_where(self):
        """
        Test that chaining multiple where clauses works results in an AND.
        """
        self.insert_rows()

        query = Band.select(
            'name'
        ).where(
            Band.name == 'raichu'
        ).where(
            Band.trainer == 'sally'
        )

        response = query.run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}]
        )
        self.assertTrue(
            'AND' in query.__str__()
        )

    def test_complex_where(self):
        """
        Test a complex where clause - combining AND, and OR.
        """
        self.insert_rows()

        response = Band.select(
            'name'
        ).where(
            ((Band.power == 2000) & (Band.trainer == 'sally')) |
            ((Band.power == 10) & (Band.trainer == 'gordon'))
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'raichu'}, {'name': 'weedle'}]
        )

    def test_limit(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).order_by(
            'name'
        ).limit(
            1
        ).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}]
        )

    def test_first(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).order_by(
            'name'
        ).first().run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            {'name': 'pikachu'}
        )

    def test_order_by_ascending(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).order_by(
            'name'
        ).limit(1).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'pikachu'}]
        )

    def test_order_by_decending(self):
        self.insert_rows()

        response = Band.select(
            'name'
        ).order_by(
            '-name'
        ).limit(1).run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'name': 'weedle'}]
        )

    def test_count(self):
        self.insert_rows()

        response = Band.select().where(
            Band.name == 'pikachu'
        ).count().run_sync()

        print(f'response = {response}')

        self.assertEqual(
            response,
            [{'count': 1}]
        )

    def test_distinct(self):
        self.insert_rows()
        self.insert_rows()

        response = Band.select('name').where(
            Band.name == 'pikachu'
        ).distinct().run_sync()

        self.assertTrue(response == [{'name': 'pikachu'}])
