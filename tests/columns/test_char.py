from piccolo.columns.column_types import Char
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest
from tests.base import engines_only


class Venue(Table):
    country_code = Char(length=2)


@engines_only("postgres", "cockroach")
class TestChar(AsyncTableTest):
    """
    SQLite doesn't enforce any constraints on max character length.

    https://www.sqlite.org/faq.html#q9
    """

    tables = [Venue]

    async def test_length(self):
        row = Venue(country_code="GB")
        await row.save()

        with self.assertRaises(Exception):
            row.country_code = "XXX"
            await row.save()

    async def test_padding(self):
        """
        Postgres returns ``Char`` columns padded with blank spaces.
        """
        row = Venue(country_code="G")
        await row.save()

        await row.refresh()
        self.assertEqual(row.country_code, "G ")
