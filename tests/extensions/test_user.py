from unittest import TestCase

from aragorm.extensions.user import User
from ..example_project.tables import DB


class _User(User):
    class Meta():
        tablename = 'user'
        db = DB


class TestUser(TestCase):

    def test_user(self):
        """
        Make sure the table can be created.
        """
        exception = None
        try:
            _User.create().run_sync()
        except Exception as e:
            exception = e
        else:
            _User.drop().run_sync()

        if exception:
            raise exception

        self.assertFalse(exception)
