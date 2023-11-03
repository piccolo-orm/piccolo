#!/bin/bash
set -e

MODULES="piccolo"
SOURCES="$MODULES tests"

echo "Running isort..."
isort --check $SOURCES
echo "-----"

echo "Running black..."
black --check $SOURCES
echo "-----"

echo "Running flake8..."
flake8 $SOURCES
echo "-----"

echo "Running mypy..."
mypy $SOURCES
echo "-----"

echo "Running slotscheck..."
# Currently doesn't work for Python 3.12 - so skipping until we can get a proper fix.
pythonVersion=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if [ "$pythonVersion" == '3.12' ]
  then
    echo "Skipping Python 3.12 for now"
  else
    python -m slotscheck $MODULES
fi

echo "-----"

echo "All passed!"
