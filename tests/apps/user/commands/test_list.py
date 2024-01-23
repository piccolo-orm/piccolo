from unittest import TestCase
from unittest.mock import AsyncMock, MagicMock, patch

from piccolo.apps.user.commands.list import list_users
from piccolo.apps.user.tables import BaseUser
from piccolo.utils.sync import run_sync


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
        run_sync(list_users())

        output = "\n".join(i.args[0] for i in print_mock.call_args_list)

        assert self.username in output
        assert self.password not in output
        assert self.user.password not in output


class TestLimit(TestCase):
    def test_non_positive(self):
        """
        Make sure non-positive `limit` values are rejected.
        """
        for value in (0, -1):
            with self.assertRaises(ValueError):
                run_sync(list_users(page=value))


class TestPage(TestCase):
    def test_non_positive(self):
        """
        Make sure non-positive `page` values are rejected.
        """
        for value in (0, -1):
            with self.assertRaises(ValueError):
                run_sync(list_users(limit=value))


class TestOrder(TestCase):
    @patch("piccolo.apps.user.commands.list.get_users")
    def test_order(self, get_users: AsyncMock):
        """
        Make sure valid column names are accepted.
        """
        get_users.return_value = []
        run_sync(list_users(order_by="email"))

        self.assertDictEqual(
            get_users.call_args.kwargs,
            {
                "order_by": BaseUser.email,
                "ascending": True,
                "limit": 20,
                "page": 1,
            },
        )

    @patch("piccolo.apps.user.commands.list.get_users")
    def test_descending(self, get_users: AsyncMock):
        """
        Make sure a colume name prefixed with '-' works.
        """
        get_users.return_value = []
        run_sync(list_users(order_by="-email"))

        self.assertDictEqual(
            get_users.call_args.kwargs,
            {
                "order_by": BaseUser.email,
                "ascending": False,
                "limit": 20,
                "page": 1,
            },
        )

    def test_unrecognised_column(self):
        """
        Make sure invalid column names are rejected.
        """
        with self.assertRaises(ValueError):
            run_sync(list_users(order_by="abc123"))
