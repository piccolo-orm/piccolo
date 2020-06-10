#!/bin/bash

cd ..

export PICCOLO_CONF="tests.postgres_conf"
python -m pytest --cov=piccolo -s $@
