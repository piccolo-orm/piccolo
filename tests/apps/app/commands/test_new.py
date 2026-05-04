import os
import shutil
import tempfile
from unittest import TestCase

from piccolo.apps.app.commands.new import (
    get_app_module,
    module_exists,
    new,
    validate_app_name,
)


class TestModuleExists(TestCase):
    def test_module_exists(self):
        self.assertEqual(module_exists("sys"), True)
        self.assertEqual(module_exists("abc123xyz"), False)


class TestNewApp(TestCase):
    def test_new(self):
        root = tempfile.gettempdir()
        app_name = "my_app"

        app_path = os.path.join(root, app_name)

        if os.path.exists(app_path):
            shutil.rmtree(app_path)

        new(app_name=app_name, root=root)

        self.assertTrue(os.path.exists(app_path))

    def test_new_with_clashing_name(self):
        """
        Test trying to create an app with the same name as a builtin Python
        package - it shouldn't be allowed.
        """
        root = tempfile.gettempdir()
        app_name = "sys"

        with self.assertRaises(SystemExit) as context:
            new(app_name=app_name, root=root)

        exception = context.exception
        self.assertTrue(
            str(exception.code).startswith(
                "A module called sys already exists"
            )
        )


class TestValidateAppName(TestCase):

    def test_validate_app_name(self):
        """
        Make sure only app names which work as valid Python package names are
        allowed.
        """
        # Should be rejected:
        for app_name in ("MY APP", "app/my_app", "my.app"):
            with self.assertRaises(ValueError):
                validate_app_name(app_name=app_name)

        # Should work fine:
        validate_app_name(app_name="music")


class TestGetAppIdentifier(TestCase):

    def test_get_app_module(self):
        """
        Make sure the the ``root`` argument is handled correctly.
        """
        self.assertEqual(
            get_app_module(app_name="music", root="."),
            "music.piccolo_app",
        )

        for root in ("apps", "./apps", "./apps/"):
            self.assertEqual(
                get_app_module(app_name="music", root=root),
                "apps.music.piccolo_app",
            )
