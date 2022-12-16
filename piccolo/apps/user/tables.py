"""
A User model, used for authentication.
"""
from __future__ import annotations

import datetime
import hashlib
import logging
import secrets
import typing as t

from piccolo.columns import Boolean, Secret, Timestamp, Varchar
from piccolo.columns.column_types import Serial
from piccolo.columns.readable import Readable
from piccolo.table import Table
from piccolo.utils.sync import run_sync

logger = logging.getLogger(__name__)


class BaseUser(Table, tablename="piccolo_user"):
    """
    Provides a basic user, with authentication support.
    """

    id: Serial
    username = Varchar(length=100, unique=True)
    password = Secret(length=255)
    first_name = Varchar(null=True)
    last_name = Varchar(null=True)
    email = Varchar(length=255, unique=True)
    active = Boolean(default=False)
    admin = Boolean(
        default=False, help_text="An admin can log into the Piccolo admin GUI."
    )
    superuser = Boolean(
        default=False,
        help_text=(
            "If True, this user can manage other users's passwords in the "
            "Piccolo admin GUI."
        ),
    )
    last_login = Timestamp(
        null=True,
        default=None,
        required=False,
        help_text="When this user last logged in.",
    )

    _min_password_length = 6
    _max_password_length = 128

    def __init__(self, **kwargs):
        # Generating passwords upfront is expensive, so might need reworking.
        password = kwargs.get("password", None)
        if password:
            if not password.startswith("pbkdf2_sha256"):
                kwargs["password"] = self.__class__.hash_password(password)
        super().__init__(**kwargs)

    @classmethod
    def get_salt(cls):
        return secrets.token_hex(16)

    @classmethod
    def get_readable(cls) -> Readable:
        """
        Used to get a readable string, representing a table row.
        """
        return Readable(template="%s", columns=[cls.username])

    ###########################################################################

    @classmethod
    def _validate_password(cls, password: str):
        """
        Validate the raw password. Used by :meth:`update_password` and
        :meth:`create_user`.

        :param password:
            The raw password e.g. ``'hello123'``.
        :raises ValueError:
            If the password fails any of the criteria.

        """
        if not password:
            raise ValueError("A password must be provided.")

        if len(password) < cls._min_password_length:
            raise ValueError("The password is too short.")

        if len(password) > cls._max_password_length:
            raise ValueError("The password is too long.")

        if password.startswith("pbkdf2_sha256"):
            logger.warning(
                "Tried to create a user with an already hashed password."
            )
            raise ValueError("Do not pass a hashed password.")

    ###########################################################################

    @classmethod
    def update_password_sync(cls, user: t.Union[str, int], password: str):
        """
        A sync equivalent of :meth:`update_password`.
        """
        return run_sync(cls.update_password(user, password))

    @classmethod
    async def update_password(cls, user: t.Union[str, int], password: str):
        """
        The password is the raw password string e.g. ``'password123'``.
        The user can be a user ID, or a username.
        """
        if isinstance(user, str):
            clause = cls.username == user
        elif isinstance(user, int):
            clause = cls.id == user
        else:
            raise ValueError(
                "The `user` arg must be a user id, or a username."
            )

        cls._validate_password(password=password)

        password = cls.hash_password(password)
        await cls.update({cls.password: password}).where(clause).run()

    ###########################################################################

    @classmethod
    def hash_password(
        cls, password: str, salt: str = "", iterations: int = 10000
    ) -> str:
        """
        Hashes the password, ready for storage, and for comparing during
        login.

        :raises ValueError:
            If an excessively long password is provided.

        """
        if len(password) > cls._max_password_length:
            logger.warning("Excessively long password provided.")
            raise ValueError("The password is too long.")

        if not salt:
            salt = cls.get_salt()
        hashed = hashlib.pbkdf2_hmac(
            "sha256",
            bytes(password, encoding="utf-8"),
            bytes(salt, encoding="utf-8"),
            iterations,
        ).hex()
        return f"pbkdf2_sha256${iterations}${salt}${hashed}"

    def __setattr__(self, name: str, value: t.Any):
        """
        Make sure that if the password is set, it's stored in a hashed form.
        """
        if name == "password" and not value.startswith("pbkdf2_sha256"):
            value = self.__class__.hash_password(value)

        super().__setattr__(name, value)

    @classmethod
    def split_stored_password(cls, password: str) -> t.List[str]:
        elements = password.split("$")
        if len(elements) != 4:
            raise ValueError("Unable to split hashed password")
        return elements

    ###########################################################################

    @classmethod
    def login_sync(cls, username: str, password: str) -> t.Optional[int]:
        """
        A sync equivalent of :meth:`login`.
        """
        return run_sync(cls.login(username, password))

    @classmethod
    async def login(cls, username: str, password: str) -> t.Optional[int]:
        """
        Make sure the user exists and the password is valid. If so, the
        ``last_login`` value is updated in the database.

        :returns:
            The id of the user if a match is found, otherwise ``None``.

        """
        if len(username) > cls.username.length:
            logger.warning("Excessively long username provided.")
            return None

        if len(password) > cls._max_password_length:
            logger.warning("Excessively long password provided.")
            return None

        response = (
            await cls.select(cls._meta.primary_key, cls.password)
            .where(cls.username == username)
            .first()
            .run()
        )
        if not response:
            # No match found
            return None

        stored_password = response["password"]

        algorithm, iterations, salt, hashed = cls.split_stored_password(
            stored_password
        )

        if (
            cls.hash_password(password, salt, int(iterations))
            == stored_password
        ):
            await cls.update({cls.last_login: datetime.datetime.now()}).where(
                cls.username == username
            )
            return response["id"]
        else:
            return None

    ###########################################################################

    @classmethod
    def create_user_sync(
        cls, username: str, password: str, **extra_params
    ) -> BaseUser:
        """
        A sync equivalent of :meth:`create_user`.
        """
        return run_sync(
            cls.create_user(
                username=username, password=password, **extra_params
            )
        )

    @classmethod
    async def create_user(
        cls, username: str, password: str, **extra_params
    ) -> BaseUser:
        """
        Creates a new user, and saves it in the database. It is recommended to
        use this rather than instantiating and saving ``BaseUser`` directly, as
        we add extra validation.

        :raises ValueError:
            If the username or password is invalid.
        :returns:
            The created ``BaseUser`` instance.

        """
        if not username:
            raise ValueError("A username must be provided.")

        cls._validate_password(password=password)

        user = cls(username=username, password=password, **extra_params)
        await user.save()
        return user
