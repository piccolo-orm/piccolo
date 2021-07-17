#!/bin/bash

isort piccolo tests
black piccolo tests --line-length 79
flake8 piccolo tests
mypy piccolo tests
