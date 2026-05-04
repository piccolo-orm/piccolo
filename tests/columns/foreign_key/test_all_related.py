from unittest import TestCase

from tests.example_apps.music.tables import Ticket


class TestAllRelated(TestCase):
    def test_all_related(self):
        """
        Make sure you can retrieve all foreign keys from a related table,
        without explicitly specifying them.
        """
        all_related = Ticket.concert.all_related()

        self.assertEqual(
            all_related,
            [
                Ticket.concert.band_1,
                Ticket.concert.band_2,
                Ticket.concert.venue,
            ],
        )

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_related[0]._meta.call_chain,
            Ticket.concert.band_1._meta.call_chain,
        )
        self.assertEqual(
            all_related[1]._meta.call_chain,
            Ticket.concert.band_2._meta.call_chain,
        )
        self.assertEqual(
            all_related[2]._meta.call_chain,
            Ticket.concert.venue._meta.call_chain,
        )

    def test_all_related_deep(self):
        """
        Make sure ``all_related`` works when the joins are several layers deep.
        """
        all_related = Ticket.concert._.band_1.all_related()
        self.assertEqual(all_related, [Ticket.concert._.band_1._.manager])

        # Make sure the call chains are also correct.
        self.assertEqual(
            all_related[0]._meta.call_chain,
            Ticket.concert._.band_1._.manager._meta.call_chain,
        )

    def test_all_related_exclude(self):
        """
        Make sure you can exclude some columns.
        """
        self.assertEqual(
            Ticket.concert.all_related(exclude=["venue"]),
            [Ticket.concert.band_1, Ticket.concert.band_2],
        )

        self.assertEqual(
            Ticket.concert.all_related(exclude=[Ticket.concert._.venue]),
            [Ticket.concert.band_1, Ticket.concert.band_2],
        )
