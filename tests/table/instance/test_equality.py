import typing as t

from piccolo.columns.column_types import UUID, Varchar
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest
from tests.example_apps.music.tables import Manager as Manager_


class ManagerUUID(Table):
    id = UUID(primary_key=True)
    name = Varchar()


class TestInstanceEquality(AsyncTableTest):
    tables: t.List[t.Union[t.Type[Manager_], t.Type[ManagerUUID]]] = [
        Manager_,
        ManagerUUID,
    ]

    async def test_instance_equality(self) -> None:
        """
        Make sure instance equality works, for tables with a `Serial` primary
        key, or a `UUID` primary key.
        """
        for Manager in self.tables:
            manager_1 = Manager(name="Guido")
            await manager_1.save()

            manager_2 = Manager(name="Graydon")
            await manager_2.save()

            self.assertEqual(manager_1, manager_1)
            self.assertNotEqual(manager_1, manager_2)

            # Try fetching the row from the database.
            manager_1_from_db = (
                await Manager.objects()
                .where(Manager.id == manager_1.id)
                .first()
            )
            self.assertEqual(manager_1, manager_1_from_db)
            self.assertNotEqual(manager_2, manager_1_from_db)

            # Try rows which haven't been saved yet.
            # They have no primary key value (because they use Serial columns
            # as the primary key), so they shouldn't be equal.
            self.assertNotEqual(Manager(), Manager())
            self.assertNotEqual(manager_1, Manager())

            # Make sure an object is equal to itself, even if not saved.
            manager_unsaved = Manager()
            self.assertEqual(manager_unsaved, manager_unsaved)
