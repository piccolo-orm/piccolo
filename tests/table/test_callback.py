from unittest.mock import Mock

from tests.base import AsyncMock, DBTestCase
from tests.example_apps.music.tables import Band


class TestNoCallback(DBTestCase):
    def test_no_callback(self):
        """
        Just check we don't get any "NoneType is not callable" kind of errors
        when we run a query without setting the callback.
        """
        self.insert_row()
        Band.select(Band.name).run_sync()


class TestCallbackSuccesses(DBTestCase):
    def test_callback_sync(self):
        self.insert_row()

        callback_handler = Mock()
        Band.select(Band.name).callback(callback_handler).run_sync()
        callback_handler.assert_called_once_with(
            True, [{"name": "Pythonistas"}]
        )

    def test_callback_async(self):
        self.insert_row()

        callback_handler = AsyncMock()
        Band.select(Band.name).callback(callback_handler).run_sync()
        callback_handler.assert_called_once_with(
            True, [{"name": "Pythonistas"}]
        )
