import os
import shutil
from unittest import TestCase

from piccolo.apps.app.commands.new import new


class TestNewApp(TestCase):
    def test_new(self):
        root = "/tmp"
        app_name = "my_app"

        app_path = os.path.join(root, app_name)

        if os.path.exists(app_path):
            shutil.rmtree(app_path)

        new(app_name=app_name, root=root)

        self.assertTrue(os.path.exists(app_path))
