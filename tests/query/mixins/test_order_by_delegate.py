from unittest import TestCase

from piccolo.query.mixins import OrderByDelegate


class TestOrderByDelegate(TestCase):
    def test_no_columns(self):
        """
        An exception should be raised if no columns are passed in.
        """
        delegate = OrderByDelegate()

        with self.assertRaises(ValueError) as manager:
            delegate.order_by()

        self.assertEqual(
            manager.exception.__str__(),
            "At least one column must be passed to order_by.",
        )
