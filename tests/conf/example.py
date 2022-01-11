"""
This file is used by test_apps.py to make sure we can exclude imported
``Table`` subclasses when using ``table_finder``.
"""
from piccolo.apps.user.tables import BaseUser
from piccolo.columns.column_types import ForeignKey, Varchar
from piccolo.table import Table


class Musician(Table):
    name = Varchar()
    user = ForeignKey(BaseUser)
