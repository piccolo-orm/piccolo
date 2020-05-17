#!/bin/bash
rm -rf ./build/*
rm ./dist/*
python setup.py sdist bdist_wheel
twine upload dist/*
