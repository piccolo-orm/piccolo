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

echo "Running pyright..."
pyright $sources
echo "-----"

echo "Running slotscheck..."
python -m slotscheck $MODULES
echo "-----"

echo "All passed!"
