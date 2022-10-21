from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.migrations.commands.check import CheckMigrationManager, check
from piccolo.conf.apps import AppRegistry
from piccolo.utils.sync import run_sync


class TestCheckMigrationCommand(TestCase):
    @patch.object(
        CheckMigrationManager,
        "get_app_registry",
    )
    def test_check_migrations(self, get_app_registry: MagicMock):
        get_app_registry.return_value = AppRegistry(
            apps=["piccolo.apps.user.piccolo_app"]
        )

        # Make sure it runs without raising an exception:
        run_sync(check())
