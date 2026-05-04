from piccolo.columns import ForeignKey, Varchar
from piccolo.columns.base import OnDelete, OnUpdate
from piccolo.query.constraints import get_fk_constraint_rules
from piccolo.table import Table
from piccolo.testing.test_case import AsyncTableTest
from tests.base import engines_only


class Manager(Table):
    name = Varchar()


class Band(Table):
    """
    Contains a ForeignKey with non-default `on_delete` and `on_update` values.
    """

    manager = ForeignKey(
        references=Manager,
        on_delete=OnDelete.set_null,
        on_update=OnUpdate.set_null,
    )


@engines_only("postgres", "cockroach")
class TestOnDeleteOnUpdate(AsyncTableTest):
    """
    Make sure that on_delete, and on_update are correctly applied in the
    database.
    """

    tables = [Manager, Band]

    async def test_on_delete_on_update(self):
        constraint_rules = await get_fk_constraint_rules(Band.manager)
        self.assertEqual(constraint_rules.on_delete, OnDelete.set_null)
        self.assertEqual(constraint_rules.on_update, OnDelete.set_null)
