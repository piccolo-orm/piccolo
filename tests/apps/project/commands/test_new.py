import os
from unittest import TestCase

from piccolo.apps.project.commands.new import new


class TestNewProject(TestCase):
    def test_new(self):
        root = "/tmp"

        file_path = "/tmp/piccolo_conf.py"

        if os.path.exists(file_path):
            os.unlink(file_path)

        new(root=root)

        self.assertTrue(os.path.exists(file_path))
