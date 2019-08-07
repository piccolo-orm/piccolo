.. _PlaygroundAdvanced:

Advanced Playground Usage
=========================

Postgres
--------

If you want to use Postgres instead of SQLite, you need to create a database
first.


Install Postgres
~~~~~~~~~~~~~~~~

See :ref:`setting_up_postgres`.

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
command (use ``piccolo playground --help`` for details).

Connecting
~~~~~~~~~~

When you have the database setup, you can connect to it as follows:

.. code-block:: bash

    piccolo playground --engine=postgres
