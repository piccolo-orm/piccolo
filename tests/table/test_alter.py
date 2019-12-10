from piccolo.columns import Integer

from ..base import DBTestCase
from ..example_project.tables import Band, Manager


class TestRename(DBTestCase):
    def _test_rename(self, column):
        self.insert_row()

        rename_query = Band.alter().rename_column(column, "rating")
        rename_query.run_sync()

        select_query = Band.raw("SELECT * FROM band")
        response = select_query.run_sync()

        column_names = response[0].keys()
        self.assertTrue(
            ("rating" in column_names) and ("popularity" not in column_names)
        )

    def test_rename_string(self):
        self._test_rename(Band.popularity)

    def test_rename_column(self):
        self._test_rename("popularity")


class TestDrop(DBTestCase):
    def _test_drop(self, column):
        self.insert_row()

        Band.alter().drop_column(column).run_sync()

        response = Band.raw("SELECT * FROM band").run_sync()

        column_names = response[0].keys()
        self.assertTrue("popularity" not in column_names)

    def test_drop_string(self):
        self._test_drop(Band.popularity)

    def test_drop_column(self):
        self._test_drop("popularity")


class TestAdd(DBTestCase):
    def test_add(self):
        """
        This needs a lot more work. Need to set values for existing rows.

        Just write the test for now ...
        """
        self.insert_row()

        add_query = Band.alter().add_column("weight", Integer())
        add_query.run_sync()

        response = Band.raw("SELECT * FROM band").run_sync()

        column_names = response[0].keys()
        self.assertTrue("weight" in column_names)

        self.assertEqual(response[0]["weight"], None)


class TestUnique(DBTestCase):
    def test_unique(self):
        unique_query = Manager.alter().set_unique(Manager.name, True)
        unique_query.run_sync()

        Manager(name="Bob").save().run_sync()

        # Make sure non-unique names work:
        Manager(name="Sally").save().run_sync()

        # Check there's a unique row error ...
        with self.assertRaises(Exception):
            Manager(name="Bob").save().run_sync()

        response = Manager.select().run_sync()
        self.assertTrue(len(response) == 2)

        # Now remove the constraint, and add a row.
        not_unique_query = Manager.alter().set_unique(Manager.name, False)
        not_unique_query.run_sync()
        Manager(name="Bob").save().run_sync()

        response = Manager.select().run_sync()
        self.assertTrue(len(response), 2)


class TestNull(DBTestCase):
    def test_null(self):
        pass


class TestMultiple(DBTestCase):
    pass
