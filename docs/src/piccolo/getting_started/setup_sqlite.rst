.. _set_up_sqlite:

Setup SQLite
============

Installation
------------

The good news is SQLite is good to go out of the box with Python.

Some Piccolo features are only available with newer SQLite versions.

.. _check_sqlite_version:

Check version
-------------

To check which SQLite version you're using, simply open a Python terminal, and
do the following:

.. code-block:: python

    >>> import sqlite3
    >>> sqlite3.sqlite_version
    '3.39.0'

The easiest way to upgrade your SQLite version is to install the latest version
of Python.
