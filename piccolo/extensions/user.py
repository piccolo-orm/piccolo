"""
A User model which can be subclassed in projects.
"""
import hashlib
import secrets
import typing as t

from piccolo.table import Table
from piccolo.columns import Varchar, Boolean


# Might change to BaseUser ... making it clearer that it needs to be
# subclassed ...
class User(Table):
    """
    The password needs to be hashed.
    """
    username = Varchar(length=100)
    password = Varchar(length=255)
    email = Varchar(length=255)
    active = Boolean(default=False)

    class Meta():
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
            ).first().run()
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


# Things to consider ...
# just have some class methods around it ...
# or some methods ...
# One problem is ... need to define a secret key to salt the hash
# When people subclass it ... can add the hash???
# Need to have the ability in a table to transform values during __init__ and
# __set__.

# I don't think you have one salt ... I think it's random each time ...
# and you use it to hash the password, and then store something like this:
# encryption_method$iterations$salt$hashed_and_salted_password
# If you know the salt ... couldn't you just regenerate rainbow tables???
