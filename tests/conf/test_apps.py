from unittest import TestCase

from piccolo.conf.apps import AppRegistry


class TestAppRegistry(TestCase):
    def test_init(self):
        AppRegistry()
