from unittest import TestCase

from piccolo.conf.apps import AppConfig


class TestAppConfig(TestCase):
    def test_init(self):
        AppConfig()
