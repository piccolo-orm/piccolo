#!/bin/bash
python setup.py sdist bdist_wheel
twine upload dist/*

