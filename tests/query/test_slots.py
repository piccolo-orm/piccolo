from unittest import TestCase

from piccolo.query.methods import (
    Alter,
    Count,
    Create,
    Delete,
    Exists,
    Insert,
    Objects,
    Raw,
    Select,
    TableExists,
    Update,
)

from ..example_app.tables import Manager


class TestSlots(TestCase):
    def test_attributes(self):
        """
        Make sure slots are working correctly - they improve performance,
        and help prevent subtle bugs.
        """
        for query_class in (
            Alter,
            Count,
            Create,
            Delete,
            Exists,
            Insert,
            Objects,
            Raw,
            Select,
            TableExists,
            Update,
        ):
            class_name = query_class.__name__

            with self.assertRaises(
                AttributeError, msg=f"{class_name} didn't raised an error"
            ):
                print(f"Setting {class_name} attribute")
                query_class(table=Manager).abc = 123
