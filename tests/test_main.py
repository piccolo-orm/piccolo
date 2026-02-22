from unittest import IsolatedAsyncioTestCase

from piccolo.apps.migrations.tables import Migration
from piccolo.main import main


class TestMain(IsolatedAsyncioTestCase):

    async def asyncTearDown(self):
        await Migration.alter().drop_table(if_exists=True)

    def test_main(self):
        # Just make sure it runs without raising any errors.
        main()
