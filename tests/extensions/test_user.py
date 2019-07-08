import asyncio
from unittest import TestCase

from piccolo.extensions.user import BaseUser
from ..example_project.tables import DB


class User(BaseUser):
    class Meta():
        tablename = 'a_user'
        db = DB


class TestCreateUserTable(TestCase):

    def test_create_user_table(self):
        """
        Make sure the table can be created.
        """
        exception = None
        try:
            User.create.run_sync()
        except Exception as e:
            exception = e
        else:
            User.drop.run_sync()

        if exception:
            raise exception

        self.assertFalse(exception)


class TestHashPassword(TestCase):

    def test_hash_password(self):
        pass


class TestLogin(TestCase):

    def setUp(self):
        User.create.run_sync()

    def tearDown(self):
        User.drop.run_sync()

    def test_login(self):
        username = "bob"
        password = "Bob123$$$"
        email = "bob@bob.com"

        save_query = User(
            username=username,
            password=password,
            email=email
        ).save

        save_query.run_sync()

        authenticated = asyncio.run(
            User.login(username, password)
        )
        self.assertTrue(authenticated is not None)

        authenticated = asyncio.run(
            User.login(username, 'blablabla')
        )
        self.assertTrue(not authenticated)
