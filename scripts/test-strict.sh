#!/bin/bash
# This runs the tests in Python's development mode:
# https://docs.python.org/3/library/devmode.html
# It shows us deprecation warnings, and asyncio warnings.

# To run all in a folder tests/
# To run all in a file tests/test_foo.py
# To run all in a class tests/test_foo.py::TestFoo
# To run a single test tests/test_foo.py::TestFoo::test_foo

export PICCOLO_CONF="tests.postgres_conf"
python -X dev -m pytest -m "not integration" -s $@
