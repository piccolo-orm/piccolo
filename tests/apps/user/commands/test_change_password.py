from unittest import TestCase
from unittest.mock import patch

from piccolo.apps.user.commands.change_password import change_password
from piccolo.apps.user.tables import BaseUser


class TestChangePassword(TestCase):
    def setUp(self):
        BaseUser.create_table(if_not_exists=True).run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    @patch(
        "piccolo.apps.user.commands.change_password.get_username",
        return_value="bob123",
    )
    @patch(
        "piccolo.apps.user.commands.change_password.get_password",
        return_value="new_password",
    )
    @patch(
        "piccolo.apps.user.commands.change_password.get_confirmed_password",
        return_value="new_password",
    )
    def test_create(self, *args, **kwargs):
        user = BaseUser(username="bob123", password="old_password")
        user.save().run_sync()

        change_password()

        self.assertTrue(
            BaseUser.login_sync(username="bob123", password="new_password")
            is not None
        )
