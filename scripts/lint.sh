#!/bin/bash

isort piccolo tests
black piccolo tests
mypy piccolo tests
flake8 piccolo tests
