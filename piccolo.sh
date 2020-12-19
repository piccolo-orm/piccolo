#!/bin/bash
# This is used for running Piccolo commands on the example project within
# tests.
export PICCOLO_CONF="tests.postgres_conf"
python -m piccolo.main $@
