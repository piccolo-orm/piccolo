import os
import shutil
import tempfile
from unittest import TestCase

from piccolo.apps.app.commands.new import module_exists, new


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
            exception.code.startswith("A module called sys already exists")
        )
