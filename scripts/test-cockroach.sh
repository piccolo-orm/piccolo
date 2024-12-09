#!/bin/bash
# To run all in a folder tests/
# To run all in a file tests/test_foo.py
# To run all in a class tests/test_foo.py::TestFoo
# To run a single test tests/test_foo.py::TestFoo::test_foo

export PICCOLO_CONF="tests.cockroach_conf"
python3 -m pytest \
    --cov=piccolo \
    --cov-report=xml \
    --cov-report=html \
    --cov-fail-under=80 \
    -m "not integration and not cockroach_array_slow" \
    -s $@
