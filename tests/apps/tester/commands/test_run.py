import os
from unittest import TestCase
from unittest.mock import MagicMock, patch

from piccolo.apps.tester.commands.run import run, set_env_var


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

    def test_raise_exception(self):
        """
        Make sure the environment variable is still reset, even if an exception
        is raised within the context manager body.
        """
        var_name = "PICCOLO_TEST_3"
        initial_value = "hello"
        new_value = "goodbye"

        os.environ[var_name] = initial_value

        class FakeException(Exception):
            pass

        try:
            with set_env_var(var_name=var_name, temp_value=new_value):
                self.assertEqual(os.environ.get(var_name), new_value)
                raise FakeException("Something went wrong ...")
        except FakeException:
            pass

        self.assertEqual(os.environ.get(var_name), initial_value)


class TestRun(TestCase):
    @patch("piccolo.apps.tester.commands.run.run_pytest")
    def test_success(self, pytest: MagicMock):
        with self.assertRaises(SystemExit):
            run(pytest_args="-s foo", piccolo_conf="my_piccolo_conf")

        pytest.assert_called_once_with(["-s", "foo"])
