import asyncio
from unittest import TestCase

from piccolo.extensions.user import User
from ..example_project.tables import DB


class _User(User):
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
            _User.create.run_sync()
        except Exception as e:
            exception = e
        else:
            _User.drop.run_sync()

        if exception:
            raise exception

        self.assertFalse(exception)


class TestHashPassword(TestCase):

    def test_hash_password(self):
        pass


class TestLogin(TestCase):

    def setUp(self):
        _User.create.run_sync()

    def tearDown(self):
        _User.drop.run_sync()

    def test_login(self):
        username = "bob"
        password = "Bob123$$$"
        email = "bob@bob.com"

        _User(
            username=username,
            password=password,
            email=email
        ).save().run_sync()

        authenticated = asyncio.run(
            _User.login(username, password)
        )
        self.assertTrue(authenticated is not None)

        authenticated = asyncio.run(
            _User.login(username, 'blablabla')
        )
        self.assertTrue(not authenticated)
