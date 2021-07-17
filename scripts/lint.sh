#!/bin/bash

isort piccolo tests
mypy piccolo tests
flake8 piccolo tests
