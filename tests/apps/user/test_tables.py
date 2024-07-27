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
        self.assertEqual(manager.exception.__str__(), "The password is too long.")


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
        self.assertTrue(authenticated == user.id)

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
            f"The password is too long. (max {BaseUser._max_password_length})",
        )

        # Test short passwords
        short_password = "abc"
        with self.assertRaises(ValueError) as manager:
            BaseUser.update_password_sync(username, short_password)
        self.assertEqual(
            manager.exception.__str__(),
            f"The password is too short. (min {BaseUser._min_password_length})",
        )

        # Test no password
        empty_password = ""
        with self.assertRaises(ValueError) as manager:
            BaseUser.update_password_sync(username, empty_password)
        self.assertEqual(
            manager.exception.__str__(),
            "A password must be provided.",
        )

        # Test hashed password
        hashed_password = "pbkdf2_sha256$abc123"
        with self.assertRaises(ValueError) as manager:
            BaseUser.update_password_sync(username, hashed_password)
        self.assertEqual(
            manager.exception.__str__(),
            "Do not pass a hashed password.",
        )


class TestCreateUserFromFixture(TestCase):
    def setUp(self):
        BaseUser.create_table().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    def test_create_user_from_fixture(self):
        the_data = {
            "id": 2,
            "username": "",
            "password": "pbkdf2_sha256$10000$19ed2c0d6cbe0868a70be6"
            "446b93ed5b$c862974665ccc25b334ed42fa7e96a41"
            "04d5ddff0c2e56e0e5b1d0efc67e9d03",
            "first_name": "",
            "last_name": "",
            "email": "",
            "active": False,
            "admin": False,
            "superuser": False,
            "last_login": None,
        }
        user = BaseUser.from_dict(the_data)
        self.assertIsInstance(user, BaseUser)
        self.assertEqual(user.password, the_data["password"])


class TestCreateUser(TestCase):
    def setUp(self):
        BaseUser.create_table().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    def test_success(self):
        user = BaseUser.create_user_sync(username="bob", password="abc123")
        self.assertTrue(isinstance(user, BaseUser))
        self.assertEqual(
            BaseUser.login_sync(username="bob", password="abc123"), user.id
        )

    @patch("piccolo.apps.user.tables.logger")
    def test_hashed_password_error(self, logger: MagicMock):
        with self.assertRaises(ValueError) as manager:
            BaseUser.create_user_sync(username="bob", password="pbkdf2_sha256$10000")

        self.assertEqual(manager.exception.__str__(), "Do not pass a hashed password.")
        self.assertEqual(
            logger.method_calls,
            [call.warning("Tried to create a user with an already hashed password.")],
        )

    def test_short_password_error(self):
        with self.assertRaises(ValueError) as manager:
            BaseUser.create_user_sync(username="bob", password="abc")

        self.assertEqual(
            manager.exception.__str__(),
            f"The password is too short. (min {BaseUser._min_password_length})",
        )

    def test_long_password_error(self):
        with self.assertRaises(ValueError) as manager:
            BaseUser.create_user_sync(
                username="bob",
                password="x" * (BaseUser._max_password_length + 1),
            )

        self.assertEqual(
            manager.exception.__str__(),
            f"The password is too long. (max {BaseUser._max_password_length})",
        )

    def test_no_username_error(self):
        with self.assertRaises(ValueError) as manager:
            BaseUser.create_user_sync(
                username=None,  # type: ignore
                password="abc123",
            )

        self.assertEqual(manager.exception.__str__(), "A username must be provided.")

    def test_no_password_error(self):
        with self.assertRaises(ValueError) as manager:
            BaseUser.create_user_sync(
                username="bob",
                password=None,  # type: ignore
            )

        self.assertEqual(manager.exception.__str__(), "A password must be provided.")


class TestAutoHashingUpdate(TestCase):
    """
    Make sure that users with passwords which were hashed in earlier Piccolo
    versions are automatically re-hashed, meeting current best practices with
    the number of hashing iterations.
    """

    def setUp(self):
        BaseUser.create_table().run_sync()

    def tearDown(self):
        BaseUser.alter().drop_table().run_sync()

    def test_hash_update(self):
        # Create a user
        username = "bob"
        password = "abc123"
        user = BaseUser.create_user_sync(username=username, password=password)

        # Update their password, so it uses less than the recommended number
        # of hashing iterations.
        BaseUser.update(
            {
                BaseUser.password: BaseUser.hash_password(
                    password=password,
                    iterations=int(BaseUser._pbkdf2_iteration_count / 2),
                )
            }
        ).where(BaseUser.id == user.id).run_sync()

        # Login the user - Piccolo should detect their password needs rehashing
        # and update it.
        self.assertIsNotNone(BaseUser.login_sync(username=username, password=password))

        user_data = (
            BaseUser.select(BaseUser.password)
            .where(BaseUser.id == user.id)
            .first()
            .run_sync()
        )
        assert user_data is not None
        hashed_password = user_data["password"]

        algorithm, iterations_, salt, hashed = BaseUser.split_stored_password(
            hashed_password
        )

        self.assertEqual(int(iterations_), BaseUser._pbkdf2_iteration_count)

        # Make sure subsequent logins work as expected
        self.assertIsNotNone(BaseUser.login_sync(username=username, password=password))
