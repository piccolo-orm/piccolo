from unittest import TestCase

from piccolo.utils.naming import _camel_to_snake


class TestCamelToSnake(TestCase):
    def test_converting_tablenames(self):
        """
        Make sure Table names are converted correctly.
        """
        self.assertEqual(_camel_to_snake("HelloWorld"), "hello_world")
        self.assertEqual(_camel_to_snake("Manager1"), "manager1")
        self.assertEqual(_camel_to_snake("ManagerAbc"), "manager_abc")
        self.assertEqual(_camel_to_snake("ManagerABC"), "manager_abc")
        self.assertEqual(_camel_to_snake("ManagerABCFoo"), "manager_abc_foo")
        self.assertEqual(_camel_to_snake("ManagerA"), "manager_a")
