#!/bin/bash
# We have a separate script for pyright vs lint.sh, as it's hard to get 100%
# success in pyright. In the future we might merge them.

set -e

MODULES="piccolo"
SOURCES="$MODULES tests"

echo "Running pyright..."
pyright $sources
echo "-----"

echo "All passed!"
