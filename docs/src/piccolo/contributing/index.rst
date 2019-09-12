.. _Contributing:

Contributing
============

If you want to dig deeper into the Piccolo internals, follow these
instructions.

Get the tests running
---------------------

 * Create a new virtualenv
 * Clone the `Git repo <https://github.com/piccolo-orm/piccolo>`_.
 * Install the dependencies: ``pip install -r requirements.txt``.
 * ``cd tests``
 * Install the test dependencies: ``pip install -r test-requirements.txt``.
 * Setup Postgres
 * Run the tests: ``./run-tests.sh``

Contributing to the docs
------------------------

The docs are written using Sphinx. To get them running locally:

 * ``cd docs``
 * Install the requirements: ``pip install -r doc-requirements.txt``
 * Do an initial build of the docs: ``make html``
 * Serve the docs: ``python serve_docs.py``
 * The docs will auto rebuild as you make changes.
