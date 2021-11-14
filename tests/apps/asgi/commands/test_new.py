import os
import shutil
import tempfile
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
