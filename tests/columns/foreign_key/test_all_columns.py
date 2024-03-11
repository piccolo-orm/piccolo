from unittest import TestCase

from tests.example_apps.music.tables import Band, Concert


class TestAllColumns(TestCase):
    def test_all_columns(self):
        """
        Make sure you can retrieve all columns from a related table, without
        explicitly specifying them.
        """
        all_columns = Band.manager.all_columns()
        self.assertEqual(all_columns, [Band.manager.id, Band.manager.name])

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_columns[0]._meta.call_chain, Band.manager.id._meta.call_chain
        )
        self.assertEqual(
            all_columns[1]._meta.call_chain, Band.manager.name._meta.call_chain
        )

    def test_all_columns_deep(self):
        """
        Make sure ``all_columns`` works when the joins are several layers deep.
        """
        all_columns = Concert.band_1._.manager.all_columns()
        self.assertEqual(all_columns, [Band.manager._.id, Band.manager._.name])

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_columns[0]._meta.call_chain,
            Concert.band_1._.manager._.id._meta.call_chain,
        )
        self.assertEqual(
            all_columns[1]._meta.call_chain,
            Concert.band_1._.manager._.name._meta.call_chain,
        )

    def test_all_columns_exclude(self):
        """
        Make sure you can exclude some columns.
        """
        self.assertEqual(
            Band.manager.all_columns(exclude=["id"]), [Band.manager.name]
        )

        self.assertEqual(
            Band.manager.all_columns(exclude=[Band.manager.id]),
            [Band.manager.name],
        )
