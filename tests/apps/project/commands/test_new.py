import os
import tempfile
from unittest import TestCase

from piccolo.apps.project.commands.new import new


class TestNewProject(TestCase):
    def test_new(self):
        root = tempfile.gettempdir()

        file_path = os.path.join(root, "piccolo_conf.py")

        if os.path.exists(file_path):
            os.unlink(file_path)

        new(root=root)

        self.assertTrue(os.path.exists(file_path))
