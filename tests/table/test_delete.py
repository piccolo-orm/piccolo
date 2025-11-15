import pytest

from piccolo.query.methods.delete import DeletionError
from tests.base import (
    DBTestCase,
    engine_version_lt,
    engines_skip,
    is_running_mysql,
    is_running_sqlite,
)
from tests.example_apps.music.tables import Band


class TestDelete(DBTestCase):
    def test_delete(self):
        self.insert_rows()

        Band.delete().where(Band.name == "CSharps").run_sync()

        response = Band.count().where(Band.name == "CSharps").run_sync()

        self.assertEqual(response, 0)

    @pytest.mark.skipif(
        is_running_mysql(),
        is_running_sqlite() and engine_version_lt(3.35),
        reason="SQLite version not supported",
    )
    def test_delete_returning(self):
        """
        Make sure delete works with the `returning` clause.
        """

        self.insert_rows()

        response = (
            Band.delete()
            .where(Band.name == "CSharps")
            .returning(Band.name)
            .run_sync()
        )

        self.assertEqual(len(response), 1)
        self.assertEqual(response, [{"name": "CSharps"}])

    def test_validation(self):
        """
        Make sure you can't delete all the data without forcing it.
        """
        with self.assertRaises(DeletionError):
            Band.delete().run_sync()

        Band.delete(force=True).run_sync()

    @engines_skip("mysql")
    def test_delete_with_joins(self):
        """
        Make sure delete works if the `where` clause specifies joins.
        TODO - MySQL does not allow deleting from a table you
        also select from. asyncmy.errors.OperationalError:
        (1093, "You can't specify target table 'band' for update in
        FROM clause")
        Look at where clause !!!
        Correct MySQL query is:
        DELETE FROM `band`
        WHERE `manager` IN (
            SELECT manager FROM (
                SELECT b.manager
                FROM `band` AS b
                LEFT JOIN `manager` AS m ON b.manager = m.id
                WHERE m.name = 'Guido'
            ) AS sub
        );
        """

        self.insert_rows()

        Band.delete().where(Band.manager._.name == "Guido").run_sync()

        response = (
            Band.count().where(Band.manager._.name == "Guido").run_sync()
        )

        self.assertEqual(response, 0)
