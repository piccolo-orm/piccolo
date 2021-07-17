#!/bin/bash

isort piccolo tests
black piccolo tests
flake8 piccolo tests
mypy piccolo tests
