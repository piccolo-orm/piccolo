.. _Contributing:

Contributing
============

If you want to dig deeper into the Piccolo internals, follow these
instructions.

-------------------------------------------------------------------------------

Running Cockroach
-----------------

To get a local Cockroach instance running, you can use:

.. code-block:: console

    cockroach start-single-node --insecure --store=type=mem,size=2GiB

Make sure the test database exists:

.. code-block:: console

    cockroach sql --insecure
    >>> create database piccolo
    >>> use piccolo

-------------------------------------------------------------------------------

Get the tests running
---------------------

* Create a new virtualenv
* Clone the `Git repo <https://github.com/piccolo-orm/piccolo>`_
* ``cd piccolo``
* Install default dependencies: ``pip install -r requirements/requirements.txt``
* Install development dependencies: ``pip install -r requirements/dev-requirements.txt``
* Install test dependencies: ``pip install -r requirements/test-requirements.txt``
* Install database drivers: ``pip install -r requirements/extras/postgres.txt -r requirements/extras/sqlite.txt``
* Setup Postgres, and make sure a database called ``piccolo`` exists (see ``tests/postgres_conf.py``).
* Run the automated code linting/formatting tools: ``./scripts/lint.sh``
* Run the test suite with Postgres: ``./scripts/test-postgres.sh``
* Run the test suite with Cockroach: ``./scripts/test-cockroach.sh``
* Run the test suite with Sqlite: ``./scripts/test-sqlite.sh``

-------------------------------------------------------------------------------

Contributing to the docs
------------------------

The docs are written using Sphinx. To get them running locally:

* Install the requirements: ``pip install -r requirements/doc-requirements.txt``
* ``cd docs``
* Do an initial build of the docs: ``make html``
* Serve the docs: ``./scripts/run-docs.sh``
* The docs will auto rebuild as you make changes.

-------------------------------------------------------------------------------

Code style
----------

Piccolo uses `Black <https://black.readthedocs.io/en/stable/>`_  for
formatting, preferably with a max line length of 79, to keep it consistent
with `PEP8 <https://python.org/dev/peps/pep-0008/>`_ .

You can configure `VSCode <https://code.visualstudio.com/>`_ by modifying
``settings.json`` as follows:

.. code-block:: json

    {
        "python.linting.enabled": true,
        "python.linting.mypyEnabled": true,
        "python.formatting.provider": "black",
        "python.formatting.blackArgs": [
            "--line-length",
            "79"
        ],
        "editor.formatOnSave": true
    }

Type hints are used throughout the project.

-------------------------------------------------------------------------------

Profiling
---------

This isn't required to contribute to Piccolo, but is useful when investigating
performance problems.

 * Install the dependencies: ``pip install requirements/profile-requirements.txt``
 * Make sure a Postgres database called ``piccolo_profile`` exists.
 * Run ``./scripts/profile.sh`` to get performance data.
