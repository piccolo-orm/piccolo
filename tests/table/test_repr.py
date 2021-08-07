from ..base import DBTestCase, postgres_only, sqlite_only
from ..example_app.tables import Manager


class TestTableRepr(DBTestCase):
    @postgres_only
    def test_repr_postgres(self):
        self.assertEqual(
            Manager().__repr__(),
            '<Manager: "id" SERIAL PRIMARY KEY NOT NULL>',
        )

        self.insert_row()
        manager = Manager.objects().first().run_sync()
        self.assertEqual(
            manager.__repr__(), f"<Manager: {Manager._meta.primary_key}>"
        )

    @sqlite_only
    def test_repr_sqlite(self):
        self.assertEqual(
            Manager().__repr__(),
            '<Manager: "id" INTEGER PRIMARY KEY NOT NULL>',
        )

        self.insert_row()
        manager = Manager.objects().first().run_sync()
        self.assertEqual(
            manager.__repr__(), f"<Manager: {Manager._meta.primary_key}>"
        )
