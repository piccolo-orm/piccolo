#!/bin/bash
# To run all in a folder tests/
# To run all in a file tests/test_foo.py
# To run all in a class tests/test_foo.py::TestFoo
# To run a single test tests/test_foo.py::TestFoo::test_foo

export PICCOLO_CONF="tests.postgres_conf"
python -m tests.utils.setup --db_engine=postgres --action=spin_up
python -m pytest --cov=piccolo --cov-report xml --cov-report html --cov-fail-under 85 -s $@
python -m tests.utils.setup --db_engine=postgres --action=tear_down
