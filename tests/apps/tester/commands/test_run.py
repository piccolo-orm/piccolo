import os
from unittest import TestCase

from piccolo.apps.tester.commands.run import set_env_var


class TestSetEnvVar(TestCase):
    def test_no_existing_value(self):
        """
        Make sure the environment variable is set correctly, when there is
        no existing value.
        """
        var_name = "PICCOLO_TEST_1"

        # Make sure it definitely doesn't exist already
        if os.environ.get(var_name) is not None:
            del os.environ[var_name]

        new_value = "hello world"

        with set_env_var(var_name=var_name, temp_value=new_value):
            self.assertEqual(os.environ.get(var_name), new_value)

        self.assertEqual(os.environ.get(var_name), None)

    def test_existing_value(self):
        """
        Make sure the environment variable is set correctly, when there is
        an existing value.
        """
        var_name = "PICCOLO_TEST_2"
        initial_value = "hello"
        new_value = "goodbye"

        os.environ[var_name] = initial_value

        with set_env_var(var_name=var_name, temp_value=new_value):
            self.assertEqual(os.environ.get(var_name), new_value)

        self.assertEqual(os.environ.get(var_name), initial_value)
