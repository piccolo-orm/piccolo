import os
import sys


def run(pytest_args: str = "", piccolo_conf: str = "piccolo_conf_test"):
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
    try:
        import pytest
    except ImportError:
        sys.exit(
            "Couldn't find pytest. Please use `pip install 'piccolo[pytest]' "
            "to use this feature."
        )

    os.environ["PICCOLO_CONF"] = piccolo_conf

    args = pytest_args.split(" ")
    sys.exit(pytest.main(args))
