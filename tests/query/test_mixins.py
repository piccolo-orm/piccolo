from unittest import TestCase

from piccolo.query.mixins import ColumnsDelegate
from tests.example_apps.music.tables import Band


class TestColumnsDelegate(TestCase):
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
