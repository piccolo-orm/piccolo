from unittest import TestCase
from unittest.mock import patch

from piccolo.apps.user.commands.create import create
from piccolo.apps.user.tables import BaseUser


class TestCreate(TestCase):
    def setUp(self):
        BaseUser.create_table(if_not_exists=True).run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    @patch(
        "piccolo.apps.user.commands.create.get_username",
        return_value="bob123",
    )
    @patch(
        "piccolo.apps.user.commands.create.get_email",
        return_value="bob@test.com",
    )
    @patch(
        "piccolo.apps.user.commands.create.get_password",
        return_value="password123",
    )
    @patch(
        "piccolo.apps.user.commands.create.get_confirmed_password",
        return_value="password123",
    )
    @patch(
        "piccolo.apps.user.commands.create.get_is_admin",
        return_value=True,
    )
    @patch(
        "piccolo.apps.user.commands.create.get_is_superuser",
        return_value=True,
    )
    @patch(
        "piccolo.apps.user.commands.create.get_is_active",
        return_value=True,
    )
    def test_create(self, *args, **kwargs):
        create()

        self.assertTrue(
            BaseUser.exists()
            .where(
                (BaseUser.admin == True)  # noqa: E712
                & (BaseUser.username == "bob123")
                & (BaseUser.email == "bob@test.com")
                & (BaseUser.superuser.eq(True))
                & (BaseUser.active.eq(True))
            )
            .run_sync()
        )

    def test_create_with_arguments(self, *args, **kwargs):
        arguments = {
            "username": "bob123",
            "email": "bob@test.com",
            "password": "password123",
            "is_admin": True,
            "is_superuser": True,
            "is_active": True,
        }
        create(**arguments)

        self.assertTrue(
            BaseUser.exists()
            .where(
                (BaseUser.admin == True)  # noqa: E712
                & (BaseUser.username == "bob123")
                & (BaseUser.email == "bob@test.com")
                & (BaseUser.superuser.eq(True))
                & (BaseUser.active.eq(True))
            )
            .run_sync()
        )
