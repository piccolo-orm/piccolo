#!/bin/bash
# This is used for running Piccolo commands on the example project within
# the tests folder. For example, if we need to add a new auto migration to it.
export PICCOLO_CONF="tests.postgres_conf"
python -m piccolo.main $@
