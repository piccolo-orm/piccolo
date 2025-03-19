import os
from unittest import TestCase

from piccolo.conf.overrides import OverrideLoader


class TestOverrideLoader(TestCase):
    def test_get_override(self):
        """
        Make sure we can get overrides from a TOML file.
        """
        loader = OverrideLoader(
            toml_file_name="test_overrides.toml",
            folder_path=os.path.join(os.path.dirname(__file__), "data"),
        )
        self.assertEqual(
            loader.get_override(
                key="MY_TEST_VALUE",
            ),
            "hello world",
        )

        self.assertIsNone(
            loader.get_override(
                key="WRONG_KEY",
            )
        )
