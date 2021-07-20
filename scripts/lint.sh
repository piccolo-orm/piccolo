#!/bin/bash

SOURCES="piccolo tests"

isort $SOURCES
black $SOURCES
flake8 $SOURCES
mypy $SOURCES
