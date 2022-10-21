import ast
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import pytest

from piccolo.apps.asgi.commands.new import ROUTERS, SERVERS, new
from tests.base import unix_only


class TestNewApp(TestCase):
    def test_new(self):
        """
        Test that the created files have the correct content. List all .py
        files inside the root directory and check if they are valid python code
        with ast.parse.
        """
        for router in ROUTERS:
            for server in SERVERS:
                with patch(
                    "piccolo.apps.asgi.commands.new.get_routing_framework",
                    return_value=router,
                ), patch(
                    "piccolo.apps.asgi.commands.new.get_server",
                    return_value=server,
                ):
                    root = os.path.join(tempfile.gettempdir(), "asgi_app")

                    if os.path.exists(root):
                        shutil.rmtree(root)

                    os.mkdir(root)
                    new(root=root)

                    # Make sure the files were created
                    self.assertTrue(
                        os.path.exists(os.path.join(root, "app.py"))
                    )

                    # Make sure the Python code is valid.
                    for file in list(Path(root).rglob("*.py")):
                        with open(os.path.join(root, file), "r") as f:
                            ast.parse(f.read())
                            f.close()


class TestNewAppRuns(TestCase):
    @unix_only
    @pytest.mark.integration
    def test_new(self):
        """
        Test that the ASGI app actually runs.
        """
        for router in ROUTERS:
            with patch(
                "piccolo.apps.asgi.commands.new.get_routing_framework",
                return_value=router,
            ), patch(
                "piccolo.apps.asgi.commands.new.get_server",
                return_value=SERVERS[0],
            ):
                root = os.path.join(tempfile.gettempdir(), "asgi_app")

                if os.path.exists(root):
                    shutil.rmtree(root)

                os.mkdir(root)
                new(root=root)

                # Copy a dummy ASGI server, so we can test that the server
                # works.
                shutil.copyfile(
                    os.path.join(
                        os.path.dirname(__file__),
                        "files",
                        "dummy_server.py",
                    ),
                    os.path.join(root, "dummy_server.py"),
                )

                response = subprocess.run(
                    f"cd {root} && "
                    "python -m venv venv && "
                    "./venv/bin/pip install -r requirements.txt && "
                    "./venv/bin/python dummy_server.py",
                    shell=True,
                )
                self.assertEqual(
                    response.returncode, 0, msg=f"{router} failed"
                )
