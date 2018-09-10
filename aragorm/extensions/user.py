"""
A User model which can be subclassed in projects.
"""
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
    def hash_password(cls, password: str) -> str:
        """
        Hashes the password, ready for storage, and for comparing during
        login.
        """
        return 'secret'

    @classmethod
    def login(cls, username: str, password: str):
        return cls.select().where(
            (cls.username == username) &
            (cls.password == cls.hash_password(password))
        ).exists()


# Things to consider ...
# just have some class methods around it ...
# or some methods ...
# One problem is ... need to define a secret key to salt the hash
# When people subclass it ... can add the hash???
# Need to have the ability in a table to transform values during __init__ and
# __set__.
# That means I don't need a create_user ...
# BUT ... I still need a check_password ...
