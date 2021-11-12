import ast
import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from piccolo.apps.asgi.commands.new import ROUTERS, SERVERS, new


class TestNewApp(TestCase):
    @patch(
        "piccolo.apps.asgi.commands.new.get_routing_framework",
        return_value=ROUTERS[0],
    )
    @patch(
        "piccolo.apps.asgi.commands.new.get_server",
        return_value=SERVERS[0],
    )
    def test_new(self, *args, **kwargs):
        root = os.path.join(tempfile.gettempdir(), "asgi_app")

        if os.path.exists(root):
            shutil.rmtree(root)

        os.mkdir(root)
        new(root=root)

        self.assertTrue(os.path.exists(os.path.join(root, "app.py")))

    @patch(
        "piccolo.apps.asgi.commands.new.get_routing_framework",
        return_value=ROUTERS[0],
    )
    @patch(
        "piccolo.apps.asgi.commands.new.get_server",
        return_value=SERVERS[0],
    )
    def test_new_created_files_content(self, *args, **kwargs):
        """
        Test that the created files have the correct content.
        list all .py files inside root directory and check
         if they are valid python code with ast.parse
        """
        root = os.path.join(tempfile.gettempdir(), "asgi_app")

        if os.path.exists(root):
            shutil.rmtree(root)

        os.mkdir(root)
        new(root=root)

        for file in list(Path(root).rglob("*.py")):
            with open(os.path.join(root, file), "r") as f:
                ast.parse(f.read())
                f.close()

    @patch(
        "piccolo.apps.asgi.commands.new.get_routing_framework",
        return_value=ROUTERS[0],
    )
    @patch(
        "piccolo.apps.asgi.commands.new.get_server",
        return_value=SERVERS[0],
    )
    def test_run_new_app(self, *args, **kwargs):
        """
        test that the created app runs correctly.
        """
        root = os.path.join(tempfile.gettempdir(), "asgi_app")

        if os.path.exists(root):
            shutil.rmtree(root)

        os.mkdir(root)
        new(root=root)

        venv_path = os.path.join(root, "venv")
        os.mkdir(venv_path)
        os.system(
            f"#!/bin/bash &&"
            f"cd {root} && virtualenv venv &&"
            f" source {venv_path}/bin/activate &&"
            f" pip install -r requirements.txt &&"
            f" python main.py"
        )
