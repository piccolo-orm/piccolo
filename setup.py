#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import os
import typing as t

from setuptools import find_packages, setup

from piccolo import __VERSION__ as VERSION

directory = os.path.abspath(os.path.dirname(__file__))

extras = ["orjson", "playground", "postgres", "sqlite", "uvloop"]


with open(os.path.join(directory, "README.md")) as f:
    LONG_DESCRIPTION = f.read()


def parse_requirement(req_path: str) -> t.List[str]:
    """
    Parse requirement file.
    Example:
        parse_requirement('requirements.txt')       # requirements/requirements.txt
        parse_requirement('extras/playground.txt')  # requirements/extras/playground.txt
    Returns:
        List[str]: list of requirements specified in the file.
    """  # noqa: E501
    with open(os.path.join(directory, "requirements", req_path)) as f:
        contents = f.read()
        return [i.strip() for i in contents.strip().split("\n")]


def extras_require() -> t.Dict[str, t.List[str]]:
    """
    Parse requirements in requirements/extras directory
    """
    extra_requirements = {
        extra: parse_requirement(os.path.join("extras", f"{extra}.txt"))
        for extra in extras
    }

    extra_requirements["all"] = list(
        itertools.chain.from_iterable(extra_requirements.values())
    )

    return extra_requirements


setup(
    name="piccolo",
    version=VERSION,
    description=(
        "A fast, user friendly ORM and query builder which supports asyncio."
    ),
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Daniel Townsend",
    author_email="dan@dantownsend.co.uk",
    python_requires=">=3.7.0",
    url="https://github.com/piccolo-orm/piccolo",
    packages=find_packages(exclude=("tests",)),
    package_data={
        "": [
            "templates/*",
            "templates/**/*",
            "templates/**/**/*",
            "templates/**/**/**/*",
        ],
        "piccolo": ["py.typed"],
    },
    project_urls={
        "Documentation": (
            "https://piccolo-orm.readthedocs.io/en/latest/index.html"
        ),
        "Source": "https://github.com/piccolo-orm/piccolo",
        "Tracker": "https://github.com/piccolo-orm/piccolo/issues",
    },
    install_requires=parse_requirement("requirements.txt"),
    extras_require=extras_require(),
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Framework :: AsyncIO",
        "Typing :: Typed",
        "Topic :: Database",
    ],
    entry_points={"console_scripts": ["piccolo = piccolo.main:main"]},
)
