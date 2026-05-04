from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.user.commands.change_permissions import (
    Level,
    change_permissions,
)
from piccolo.apps.user.tables import BaseUser
from piccolo.utils.sync import run_sync


class TestChangePassword(TestCase):
    def setUp(self):
        BaseUser.create_table(if_not_exists=True).run_sync()

        BaseUser(
            username="bob",
            password="bob123",
            first_name="Bob",
            last_name="Jones",
            email="bob@gmail.com",
            active=False,
            admin=False,
            superuser=False,
        ).save().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    @patch("piccolo.apps.user.commands.change_permissions.colored_string")
    def test_user_doesnt_exist(self, colored_string: MagicMock):
        run_sync(change_permissions(username="sally"))
        colored_string.assert_called_once_with(
            "User sally doesn't exist!", level=Level.medium
        )

    def test_admin(self):
        run_sync(change_permissions(username="bob", admin=True))
        self.assertTrue(
            BaseUser.exists()
            .where(BaseUser.username == "bob", BaseUser.admin.eq(True))
            .run_sync()
        )

    def test_active(self):
        run_sync(change_permissions(username="bob", active=True))
        self.assertTrue(
            BaseUser.exists()
            .where(BaseUser.username == "bob", BaseUser.active.eq(True))
            .run_sync()
        )

    def test_superuser(self):
        run_sync(change_permissions(username="bob", superuser=True))
        self.assertTrue(
            BaseUser.exists()
            .where(BaseUser.username == "bob", BaseUser.superuser.eq(True))
            .run_sync()
        )

    @patch("piccolo.apps.user.commands.change_permissions.colored_string")
    def test_no_params(self, colored_string):
        run_sync(change_permissions(username="bob"))
        colored_string.assert_called_once_with(
            "No changes detected", level=Level.medium
        )
