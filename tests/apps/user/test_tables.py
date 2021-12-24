import secrets
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from piccolo.apps.user.tables import BaseUser


class TestCreateUserTable(TestCase):
    def test_create_user_table(self):
        """
        Make sure the table can be created.
        """
        exception = None
        try:
            BaseUser.create_table().run_sync()
        except Exception as e:
            exception = e
        else:
            BaseUser.alter().drop_table().run_sync()

        if exception:
            raise exception

        self.assertFalse(exception)


class TestInstantiateUser(TestCase):
    def setUp(self):
        BaseUser.create_table().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    def test_valid_credentials(self):
        BaseUser(username="bob", password="abc123%£1pscl")

    def test_malicious_password(self):
        malicious_password = secrets.token_urlsafe(1000)
        with self.assertRaises(ValueError) as manager:
            BaseUser(username="bob", password=malicious_password)
        self.assertEqual(
            manager.exception.__str__(), "The password is too long."
        )


class TestLogin(TestCase):
    def setUp(self):
        BaseUser.create_table().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    @patch("piccolo.apps.user.tables.logger")
    def test_login(self, logger: MagicMock):
        username = "bob"
        password = "Bob123$$$"
        email = "bob@bob.com"

        user = BaseUser(username=username, password=password, email=email)
        user.save().run_sync()

        # Test correct password
        authenticated = BaseUser.login_sync(username, password)
        self.assertTrue(authenticated == user.id)  # type: ignore

        # Test incorrect password
        authenticated = BaseUser.login_sync(username, "blablabla")
        self.assertTrue(authenticated is None)

        # Test ultra long password
        malicious_password = secrets.token_urlsafe(1000)
        authenticated = BaseUser.login_sync(username, malicious_password)
        self.assertTrue(authenticated is None)
        self.assertEqual(
            logger.method_calls,
            [call.warning("Excessively long password provided.")],
        )

        # Test ulta long username
        logger.reset_mock()
        malicious_username = secrets.token_urlsafe(1000)
        authenticated = BaseUser.login_sync(malicious_username, password)
        self.assertTrue(authenticated is None)
        self.assertEqual(
            logger.method_calls,
            [call.warning("Excessively long username provided.")],
        )

    def test_update_password(self):
        username = "bob"
        password = "Bob123$$$"
        email = "bob@bob.com"

        user = BaseUser(username=username, password=password, email=email)
        user.save().run_sync()

        authenticated = BaseUser.login_sync(username, password)
        self.assertTrue(authenticated is not None)

        # Test success
        new_password = "XXX111"
        BaseUser.update_password_sync(username, new_password)
        authenticated = BaseUser.login_sync(username, new_password)
        self.assertTrue(authenticated is not None)

        # Test ultra long password
        malicious_password = secrets.token_urlsafe(1000)
        with self.assertRaises(ValueError) as manager:
            BaseUser.update_password_sync(username, malicious_password)
        self.assertEqual(
            manager.exception.__str__(),
            "The password is too long.",
        )
