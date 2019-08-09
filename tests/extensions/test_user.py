import asyncio
from unittest import TestCase

from piccolo.extensions.user import BaseUser
from ..example_project.tables import DB


class User(BaseUser):
    class Meta():
        db = DB
        tablename = 'custom_user'


class TestCreateUserTable(TestCase):

    def test_create_user_table(self):
        """
        Make sure the table can be created.
        """
        exception = None
        try:
            User.create().run_sync()
        except Exception as e:
            exception = e
        else:
            User.drop().run_sync()

        if exception:
            raise exception

        self.assertFalse(exception)


class TestHashPassword(TestCase):

    def test_hash_password(self):
        pass


class TestLogin(TestCase):

    def setUp(self):
        User.create().run_sync()

    def tearDown(self):
        User.drop().run_sync()

    def test_login(self):
        username = "bob"
        password = "Bob123$$$"
        email = "bob@bob.com"

        user = User(
            username=username,
            password=password,
            email=email
        )

        save_query = user.save()

        save_query.run_sync()

        authenticated = asyncio.run(
            User.login(username, password)
        )
        self.assertTrue(authenticated is not None)

        authenticated = asyncio.run(
            User.login(username, 'blablabla')
        )
        self.assertTrue(not authenticated)

    def test_update_password(self):
        username = "bob"
        password = "Bob123$$$"
        email = "bob@bob.com"

        user = User(
            username=username,
            password=password,
            email=email
        )
        user.save().run_sync()

        authenticated = User.login_sync(username, password)
        self.assertTrue(authenticated is not None)

        new_password = "XXX111"
        User.update_password_sync(username, new_password)
        authenticated = User.login_sync(username, new_password)
        self.assertTrue(authenticated is not None)
