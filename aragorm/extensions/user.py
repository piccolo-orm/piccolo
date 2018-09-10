"""
A User model which can be subclassed in projects.
"""
from aragorm.table import Table
from aragorm.columns import Varchar, PrimaryKey, Boolean


class User(Table):
    """
    The password needs to be hashed.
    """
    id = PrimaryKey()
    username = Varchar(length=100)
    password = Varchar(length=255)
    email = Varchar(length=255)
    active = Boolean(default=False)
