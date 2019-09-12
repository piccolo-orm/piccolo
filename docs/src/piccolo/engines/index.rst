..  _Engines:

Engines
=======

Engines are what execute the SQL queries. Each supported backend has its own
engine (see  :ref:`EngineTypes`).

It's important that each ``Table`` class knows which engine to use. There are
two ways of doing this - setting it explicitly via the ``db`` argument, or
letting Piccolo find it using ``engine_finder``.

Explicit
--------

.. code-block:: python

    from piccolo.engine.sqlite import SQLiteEngine
    from piccolo.tables import Table
    from piccolo.columns import Varchar


    DB = SQLiteEngine(path='my_db.sqlite')


    # Here we explicitly reference an engine:
    class MyTable(Table, db=DB):
        name = Varchar()


engine_finder
-------------

By default Piccolo uses ``engine_finder``. Piccolo will look for a file called
``piccolo_conf.py`` on the path, and will try and import a ``DB`` variable,
which defines the engine.

Here's an example config file:

.. code-block:: python

    # piccolo_conf.py
    from piccolo.engine.sqlite import SQLiteEngine


    DB = SQLiteEngine(path='my_db.sqlite')

.. hint:: A good place for your config files is at the root of your project,
    where the Python interpreter will be launched.

PICCOLO_CONF environment variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can modify the configuration file location by using the ``PICCOLO_CONF``
environment variable.

In your terminal:

.. code-block:: bash

    export PICCOLO_CONF=piccolo_conf_test

Or at the entypoint for your app, before any other imports:

.. code-block:: python

    import os
    os.environ['PICCOLO_CONF'] = 'piccolo_conf_test'


This is helpful during tests - you can specify a different configuration file
which contains the connection details for a test database. Similarly,
it's useful if you're deploying your code to different environments (e.g.
staging and production). Have two configuration files, and set the environment
variable accordingly.

.. code-block:: python

    # An example piccolo_conf_test.py
    from piccolo.engine.sqlite import SQLiteEngine


    DB = SQLiteEngine(path='my_test_db.sqlite')

.. hint:: You can also specify sub modules, like `my_module.piccolo_conf`.

.. _EngineTypes:

Engine types
------------

SQLiteEngine
~~~~~~~~~~~~

.. code-block:: python

    from piccolo.engine.sqlite import SQLiteEngine


    DB = SQLiteEngine(path='my_app.sqlite')


PostgresEngine
~~~~~~~~~~~~~~

.. code-block:: python

    from piccolo.engine.postgres import PostgresEngine


    DB = PostgresEngine({
        'host': 'localhost',
        'database': 'my_app',
        'user': 'postgres',
        'password': ''
    })

Connection pool
---------------

.. warning:: This is currently only available for Postgres.


To use a connection pool, you need to first initialise it. The best place to do
this is in the startup event handler of whichever web framework you are using.

Here's an example using Starlette. Notice that we also close the connection
pool in the shutdown event handler.

.. code-block:: python

    from piccolo.engine import from starlette.applications import Starlette
    from starlette.applications import Starlette


    app = Starlette()


    @app.on_event('startup')
    async def open_database_connection_pool():
        engine = engine_finder()
        await engine.start_connnection_pool()


    @app.on_event('shutdown')
    async def close_database_connection_pool():
        engine = engine_finder()
        await engine.close_connnection_pool()

.. hint:: Using a connection pool helps with performance, since connections
    are reused instead of being created for each query.

Once a connection pool has been started, the engine will use it for making
queries.

.. hint:: If you're running several instances of an app on the same server,
    you may prefer an external connection pooler - like pgbouncer.

Configuration
~~~~~~~~~~~~~

The connection pool uses the same configuration as your engine. You can also
pass in additional parameters, which are passed to the underlying database
adapter. Here's an example:

.. code-block:: python

    # To increase the number of connections available:
    await engine.start_connnection_pool(max_size=20)
