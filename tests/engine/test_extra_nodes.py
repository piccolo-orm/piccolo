from unittest import TestCase
from unittest.mock import MagicMock

from piccolo.columns.column_types import Varchar
from piccolo.engine import engine_finder
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table
from tests.base import AsyncMock, engines_only


@engines_only("postgres", "cockroach")
class TestExtraNodes(TestCase):
    def test_extra_nodes(self):
        """
        Make sure that other nodes can be queried.
        """
        # Get the test database credentials:
        test_engine = engine_finder()

        EXTRA_NODE = MagicMock(spec=PostgresEngine(config=test_engine.config))
        EXTRA_NODE.run_querystring = AsyncMock(return_value=[])

        DB = PostgresEngine(
            config=test_engine.config, extra_nodes={"read_1": EXTRA_NODE}
        )

        class Manager(Table, db=DB):
            name = Varchar()

        # Make sure the node is queried
        Manager.select().run_sync(node="read_1")
        self.assertTrue(EXTRA_NODE.run_querystring.called)

        # Make sure that a non existent node raises an error
        with self.assertRaises(KeyError):
            Manager.select().run_sync(node="read_2")
