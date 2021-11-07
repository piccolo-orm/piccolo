#!/bin/bash
SOURCES="piccolo tests"

echo "Running isort..."
isort $SOURCES
echo "-----"

echo "Running black..."
black $SOURCES
