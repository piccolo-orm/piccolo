import time  # For time travel queries.

from piccolo.query.mixins import ColumnsDelegate
from tests.base import DBTestCase, engines_only
from tests.example_apps.music.tables import Band


class TestColumnsDelegate(DBTestCase):
    def test_list_unpacking(self):
        """
        The ``ColumnsDelegate`` should unpack a list of columns if passed in by
        mistake, without the user unpacking them explicitly.

        .. code-block:: python

            # These two should both work the same:
            await Band.select([Band.id, Band.name]).run()
            await Band.select(Band.id, Band.name).run()

        """
        columns_delegate = ColumnsDelegate()

        columns_delegate.columns([Band.name])
        self.assertEqual(columns_delegate.selected_columns, [Band.name])

        columns_delegate.columns([Band.id])
        self.assertEqual(
            columns_delegate.selected_columns, [Band.name, Band.id]
        )

    @engines_only("cockroach")
    def test_as_of(self):
        """
        Time travel queries using "As Of" syntax.
        Currently supports Cockroach using AS OF SYSTEM TIME.
        """
        self.insert_rows()
        time.sleep(1)  # Ensure time travel queries have some history to use!

        result = (
            Band.select()
            .where(Band.name == "Pythonistas")
            .as_of("-500ms")
            .limit(1)
        )
        self.assertTrue("AS OF SYSTEM TIME '-500ms'" in str(result))
        result = result.run_sync()

        self.assertTrue(result[0]["name"] == "Pythonistas")

        result = Band.select().as_of()
        self.assertTrue("AS OF SYSTEM TIME '-1s'" in str(result))
        result = result.run_sync()

        self.assertTrue(result[0]["name"] == "Pythonistas")

        # Alternative syntax.
        result = Band.objects().get(Band.name == "Pythonistas").as_of("-1s")
        self.assertTrue("AS OF SYSTEM TIME '-1s'" in str(result))
        result = result.run_sync()

        self.assertTrue(result.name == "Pythonistas")
