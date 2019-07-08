"""
A User model, used for authentication.
"""
import hashlib
import secrets
import typing as t

from piccolo.table import Table
from piccolo.columns import Varchar, Boolean


class BaseUser(Table):
    """
    Subclass this table in your own project, so Meta.db can be defined.
    """
    username = Varchar(length=100)
    password = Varchar(length=255)
    email = Varchar(length=255)
    active = Boolean(default=False)
    admin = Boolean(default=False)

    class Meta():
        # This is required because 'user' is a reserved keyword in SQL, so
        # using it as a tablename causes issues.
        tablename = 'a_user'

    def __init__(self, **kwargs):
        """
        Generating passwords upfront is expensive, so might need reworking.
        """
        password = kwargs.get('password', None)
        if password:
            kwargs['password'] = self.__class__.hash_password(password)
        super().__init__(**kwargs)

    @classmethod
    def get_salt(cls):
        return secrets.token_hex(16)

    @classmethod
    def hash_password(
        cls,
        password: str,
        salt: str = '',
        iterations: int = 10000
    ) -> str:
        """
        Hashes the password, ready for storage, and for comparing during
        login.
        """
        if salt == '':
            salt = cls.get_salt()
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            bytes(password, encoding="utf-8"),
            bytes(salt, encoding="utf-8"),
            iterations
        ).hex()
        return f'pbkdf2_sha256${iterations}${salt}${hashed}'

    @classmethod
    def split_stored_password(self, password: str) -> t.List[str]:
        elements = password.split('$')
        if len(elements) != 4:
            raise ValueError('Unable to split hashed password')
        return elements

    @classmethod
    async def login(cls, username: str, password: str) -> t.Optional[int]:
        """
        Returns the user_id if a match is found.
        """
        try:
            response = await cls.select.columns(cls.id, cls.password).where(
                (cls.username == username)
            ).first.run()
        except ValueError:
            # No match found
            return None

        stored_password = response['password']

        algorithm, iterations, salt, hashed = cls.split_stored_password(
            stored_password
        )

        if cls.hash_password(
            password,
            salt,
            int(iterations)
        ) == stored_password:
            return response['id']
        else:
            return None
