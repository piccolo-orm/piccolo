#!/bin/bash
# To run all in a folder tests/
# To run all in a file tests/test_foo.py
# To run all in a class tests/test_foo.py::TestFoo
# To run a single test tests/test_foo.py::TestFoo::test_foo

export PICCOLO_CONF="tests.mysql_conf"
python -m pytest \
    --cov=piccolo \
    --cov-report=xml \
    --cov-report=html \
    --cov-fail-under=75 \
    -m "not integration" \
    -s $@