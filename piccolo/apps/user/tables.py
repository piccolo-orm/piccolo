"""
A User model, used for authentication.
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import typing as t

from piccolo.columns import Boolean, Secret, Timestamp, Varchar
from piccolo.columns.readable import Readable
from piccolo.table import Table
from piccolo.utils.sync import run_sync

logger = logging.getLogger(__file__)


class BaseUser(Table, tablename="piccolo_user"):
    """
    Provides a basic user, with authentication support.
    """

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

    _max_password_length = 128

    def __init__(self, **kwargs):
        # Generating passwords upfront is expensive, so might need reworking.
        password = kwargs.get("password", None)
        if password:
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
    def update_password_sync(cls, user: t.Union[str, int], password: str):
        return run_sync(cls.update_password(user, password))

    @classmethod
    async def update_password(cls, user: t.Union[str, int], password: str):
        """
        The password is the raw password string e.g. password123.
        The user can be a user ID, or a username.
        """
        if isinstance(user, str):
            clause = cls.username == user
        elif isinstance(user, int):
            clause = cls.id == user  # type: ignore
        else:
            raise ValueError(
                "The `user` arg must be a user id, or a username."
            )

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

        if salt == "":
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

    @classmethod
    def login_sync(cls, username: str, password: str) -> t.Optional[int]:
        """
        Returns the user_id if a match is found.
        """
        return run_sync(cls.login(username, password))

    @classmethod
    async def login(cls, username: str, password: str) -> t.Optional[int]:
        """
        Returns the user_id if a match is found.
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
            return response["id"]
        else:
            return None
