from unittest import TestCase

from tests.base import engines_skip

from .base import M2MBase


@engines_skip("sqlite")
class TestM2MWithSchema(M2MBase, TestCase):
    """
    Make sure that when the tables exist in a non-public schema, that M2M still
    works.
    """

    def setUp(self):
        return self._setUp(schema="schema_1")
