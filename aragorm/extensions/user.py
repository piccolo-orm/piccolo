"""
A User model which can be subclassed in projects.
"""
import hashlib
import secrets
from typing import Tuple

from aragorm.table import Table
from aragorm.columns import Varchar, PrimaryKey, Boolean


# Might change to BaseUser ... making it clearer that it needs to be
# subclassed ...
class User(Table):
    """
    The password needs to be hashed.
    """
    id = PrimaryKey()
    username = Varchar(length=100)
    password = Varchar(length=255)
    email = Varchar(length=255)
    active = Boolean(default=False)

    @classmethod
    def get_salt(cls):
        return secrets.token_hex(16)

    @classmethod
    def hash_password(cls, password: str, salt: str = '') -> str:
        """
        Hashes the password, ready for storage, and for comparing during
        login.
        """
        if salt == '':
            salt = cls.get_salt()
        return hashlib.pbkdf2_hmac(
            'sha256',
            bytes(password, encoding="utf-8"),
            bytes(salt, encoding="utf-8"),
            iterations=100000
        ).decode('utf-8')

    @classmethod
    def split_hashed_password(self, hashed_password: str) -> Tuple[str]:
        return ('a', 'b', 'c')

    @classmethod
    def login(cls, username: str, password: str):
        hashed_password = cls.select('password').where(
            (cls.username == username) &
            (cls.password == cls.hash_password(password))
        ).first()


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
