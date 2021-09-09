import os
import tempfile
import uuid
from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.schema.commands.graph import graph


class TestGraph(TestCase):
    def _verify_contents(self, file_contents: str):
        """
        Make sure the contents of the file are correct.
        """
        # Make sure no extra content was output at the start.
        self.assertTrue(file_contents.startswith("digraph model_graph"))

        # Make sure the tables are present
        self.assertTrue("TABLE_Band [label" in file_contents)
        self.assertTrue("TABLE_Manager [label" in file_contents)

        # Make sure a relation is present
        self.assertTrue("TABLE_Concert -> TABLE_Band" in file_contents)

    @patch("piccolo.apps.schema.commands.graph.print")
    def test_graph(self, print_: MagicMock):
        """
        Make sure the file contents can be printed to stdout.
        """
        graph()
        file_contents = print_.call_args.args[0]
        self._verify_contents(file_contents)

    def test_graph_to_file(self):
        """
        Make sure the file contents can be written to disk.
        """
        directory = tempfile.gettempdir()
        path = os.path.join(directory, f"{uuid.uuid4()}.dot")

        graph(output=path)

        with open(path, "r") as f:
            file_contents = f.read()

        self._verify_contents(file_contents)
        os.unlink(path)
