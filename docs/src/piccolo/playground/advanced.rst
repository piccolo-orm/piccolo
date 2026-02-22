.. _PlaygroundAdvanced:

Advanced Playground Usage
=========================

Postgres
--------

If you want to use Postgres instead of SQLite, you need to create a database
first.


Install Postgres
~~~~~~~~~~~~~~~~

See :ref:`the docs on settings up Postgres <setting_up_postgres>`.

Create database
~~~~~~~~~~~~~~~

By default the playground expects a local database to exist with the following
credentials:


.. code-block:: bash

    user: "piccolo"
    password: "piccolo"
    host: "localhost"  # or 127.0.0.1
    database: "piccolo_playground"
    port: 5432

You can create a database using `pgAdmin <https://www.pgadmin.org/>`_.

If you want to use different credentials, you can pass them into the playground
command (use ``piccolo playground run --help`` for details).

Connecting
~~~~~~~~~~

When you have the database setup, you can connect to it as follows:

.. code-block:: bash

    piccolo playground run --engine=postgres

CockroachDB
-----------

If you want to use CockroachDB instead of SQLite, you need to create a database
first.


Install CockroachDB
~~~~~~~~~~~~~~~~~~~

See the `installation guide for your OS <https://www.cockroachlabs.com/docs/v25.2/install-cockroachdb-linux/>`_.

Create database
~~~~~~~~~~~~~~~
The playground is for testing and learning purposes only, so you can start a CockroachDB
`single node with the insecure flag <https://www.cockroachlabs.com/docs/v25.2/cockroach-start-single-node.html/>`_
(for non-production testing only) like this:

.. code-block:: bash

    cockroach start-single-node --insecure

After that, in a new terminal window, you can create a database like this:

.. code-block:: bash

    cockroach sql --insecure --execute="DROP DATABASE IF EXISTS piccolo_playground CASCADE;CREATE DATABASE piccolo_playground;"

By default the playground expects a local database to exist with the following
credentials:


.. code-block:: bash

    user: "root"
    password: ""
    host: "localhost"  # or 127.0.0.1
    database: "piccolo_playground"
    port: 26257


Connecting
~~~~~~~~~~

When you have the database setup, you can connect to it as follows:

.. code-block:: bash

    piccolo playground run --engine=cockroach

iPython
-------

The playground is built on top of iPython. We provide sensible defaults out of
the box for syntax highlighting etc. However, to use your own custom iPython
profile (located in ``~/.ipython``), do the following:

.. code-block:: bash

    piccolo playground run --ipython_profile

See the `iPython docs <https://ipython.readthedocs.io/en/stable/config/intro.html>`_
for more information.
