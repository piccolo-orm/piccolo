from __future__ import annotations

import os
import sys
import typing as t


class set_env_var:
    def __init__(self, var_name: str, temp_value: str):
        """
        Temporarily set an environment variable.

        :param var_name:
            The name of the environment variable to temporarily change.
        :temp_value:
            The value that the environment variable will temporarily be set to,
            before being reset to it's pre-existing value.

        """
        self.var_name = var_name
        self.temp_value = temp_value

    def set_var(self, value: str):
        os.environ[self.var_name] = value

    def get_var(self) -> t.Optional[str]:
        return os.environ.get(self.var_name)

    def __enter__(self):
        self.existing_value = self.get_var()
        self.set_var(self.temp_value)

    def __exit__(self, *args):
        if self.existing_value is None:
            del os.environ[self.var_name]
        else:
            self.set_var(self.existing_value)


def run_pytest(pytest_args: t.List[str]) -> int:  # pragma: no cover
    try:
        import pytest
    except ImportError:
        sys.exit(
            "Couldn't find pytest. Please use `pip install 'piccolo[pytest]' "
            "to use this feature."
        )

    return pytest.main(pytest_args)


def run(
    pytest_args: str = "", piccolo_conf: str = "piccolo_conf_test"
) -> None:
    """
    Run your unit test suite using Pytest.

    :param piccolo_conf:
        The piccolo_conf module to use when running your tests. This will
        contain the database settings you want to use. For example
        `my_folder.piccolo_conf_test`.
    :param pytest_args:
        Any options you want to pass to Pytest. For example
        `piccolo tester run --pytest_args="-s"`.

    """
    with set_env_var(var_name="PICCOLO_CONF", temp_value=piccolo_conf):
        args = pytest_args.split(" ")
        sys.exit(run_pytest(args))
