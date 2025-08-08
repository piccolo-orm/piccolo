from unittest.mock import Mock

from tests.base import AsyncMock, DBTestCase
from tests.example_apps.music.tables import Band


def identity(x):
    """Returns the input. Used as the side effect for mock callbacks."""
    return x


def get_name(results):
    return results["name"]


async def uppercase(name):
    """Async to ensure coroutines are called correctly."""
    return name.upper()


def limit(name):
    return name[:6]


class TestNoCallbackSelect(DBTestCase):
    def test_no_callback(self):
        """
        Just check we don't get any "NoneType is not callable" kind of errors
        when we run a select query without setting any callbacks.
        """
        self.insert_row()
        Band.select(Band.name).run_sync()


class TestNoCallbackObjects(DBTestCase):
    def test_no_callback(self):
        """
        Just check we don't get any "NoneType is not callable" kind of errors
        when we run an objects query without setting any callbacks.
        """
        self.insert_row()
        Band.objects().run_sync()


class TestCallbackSuccessesSelect(DBTestCase):
    def test_callback_sync(self):
        self.insert_row()

        callback_handler = Mock(return_value="it worked")
        result = Band.select(Band.name).callback(callback_handler).run_sync()
        callback_handler.assert_called_once_with([{"name": "Pythonistas"}])
        self.assertEqual(result, "it worked")

    def test_callback_async(self):
        self.insert_row()

        callback_handler = AsyncMock(return_value="it worked")
        result = Band.select(Band.name).callback(callback_handler).run_sync()
        callback_handler.assert_called_once_with([{"name": "Pythonistas"}])
        self.assertEqual(result, "it worked")


class TestCallbackSuccessesObjects(DBTestCase):
    def test_callback_sync(self):
        self.insert_row()

        callback_handler = Mock(return_value="it worked")
        result = Band.objects().callback(callback_handler).run_sync()
        callback_handler.assert_called_once()

        args = callback_handler.call_args[0][0]
        self.assertIsInstance(args, list)
        self.assertIsInstance(args[0], Band)
        self.assertEqual(args[0].name, "Pythonistas")
        self.assertEqual(result, "it worked")

    def test_callback_async(self):
        self.insert_row()

        callback_handler = AsyncMock(return_value="it worked")
        result = Band.objects().callback(callback_handler).run_sync()
        callback_handler.assert_called_once()

        args = callback_handler.call_args[0][0]
        self.assertIsInstance(args, list)
        self.assertIsInstance(args[0], Band)
        self.assertEqual(args[0].name, "Pythonistas")
        self.assertEqual(result, "it worked")


class TestMultipleCallbacksSelect(DBTestCase):
    def test_all_sync(self):
        self.insert_row()

        handlers = [
            Mock(side_effect=identity),
            Mock(side_effect=identity),
            Mock(side_effect=identity),
        ]
        Band.select(Band.name).callback(handlers).run_sync()

        for handler in handlers:
            handler.assert_called_once_with([{"name": "Pythonistas"}])

    def test_all_sync_chained(self):
        self.insert_row()

        handlers = [
            Mock(side_effect=identity),
            Mock(side_effect=identity),
            Mock(side_effect=identity),
        ]

        (
            Band.select(Band.name)
            .callback(handlers[0])
            .callback(handlers[1])
            .callback(handlers[2])
            .run_sync()
        )

        for handler in handlers:
            handler.assert_called_once_with([{"name": "Pythonistas"}])

    def test_all_async(self):
        self.insert_row()

        handlers = [
            AsyncMock(side_effect=identity),
            AsyncMock(side_effect=identity),
            AsyncMock(side_effect=identity),
        ]
        Band.select(Band.name).callback(handlers).run_sync()

        for handler in handlers:
            handler.assert_called_once_with([{"name": "Pythonistas"}])

    def test_all_async_chained(self):
        self.insert_row()

        handlers = [
            AsyncMock(side_effect=identity),
            AsyncMock(side_effect=identity),
            AsyncMock(side_effect=identity),
        ]
        (
            Band.select(Band.name)
            .callback(handlers[0])
            .callback(handlers[1])
            .callback(handlers[2])
            .run_sync()
        )
        for handler in handlers:
            handler.assert_called_once_with([{"name": "Pythonistas"}])

    def test_mixed(self):
        self.insert_row()

        handlers = [
            Mock(side_effect=identity),
            AsyncMock(side_effect=identity),
            Mock(side_effect=identity),
        ]
        Band.select(Band.name).callback(handlers).run_sync()

        for handler in handlers:
            handler.assert_called_once_with([{"name": "Pythonistas"}])

    def test_mixed_chained(self):
        self.insert_row()

        handlers = [
            Mock(side_effect=identity),
            AsyncMock(side_effect=identity),
            Mock(side_effect=identity),
        ]

        (
            Band.select(Band.name)
            .callback(handlers[0])
            .callback(handlers[1])
            .callback(handlers[2])
            .run_sync()
        )

        for handler in handlers:
            handler.assert_called_once_with([{"name": "Pythonistas"}])


class TestCallbackTransformDataSelect(DBTestCase):
    def test_transform(self):
        self.insert_row()

        result = (
            Band.select(Band.name)
            .first()
            .callback([get_name, uppercase, limit])
            .run_sync()
        )

        self.assertEqual(result, "PYTHON")

    def test_transform_chain(self):
        self.insert_row()

        result = (
            Band.select(Band.name)
            .first()
            .callback(get_name)
            .callback(uppercase)
            .callback(limit)
            .run_sync()
        )

        self.assertEqual(result, "PYTHON")

    def test_transform_mixed(self):
        self.insert_row()

        result = (
            Band.select(Band.name)
            .first()
            .callback([get_name, uppercase])
            .callback(limit)
            .run_sync()
        )

        self.assertEqual(result, "PYTHON")
