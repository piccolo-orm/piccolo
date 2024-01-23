from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.user.commands.list import list_users
from piccolo.apps.user.tables import BaseUser


class TestList(TestCase):
    def setUp(self):
        BaseUser.create_table(if_not_exists=True).run_sync()
        self.username = "test_user"
        self.password = "abc123XYZ"
        self.user = BaseUser.create_user_sync(
            username=self.username, password=self.password
        )

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    @patch("piccolo.utils.printing.print")
    def test_list(self, print_mock: MagicMock):
        """
        Make sure the user information is listed, excluding the password.
        """
        list_users()

        output = "\n".join(i.args[0] for i in print_mock.call_args_list)

        assert self.username in output
        assert self.password not in output
        assert self.user.password not in output


class TestListArgs(TestCase):
    def test_limit(self):
        """
        Make sure non-positive `limit` values are rejected.
        """
        for value in (0, -1):
            with self.assertRaises(ValueError):
                list_users(page=value)

    def test_page(self):
        """
        Make sure non-positive `page` values are rejected.
        """
        for value in (0, -1):
            with self.assertRaises(ValueError):
                list_users(limit=value)
