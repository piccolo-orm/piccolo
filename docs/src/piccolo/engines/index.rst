..  _Engines:

Engines
=======

Engines are what execute the SQL queries. Each supported backend has its own
engine.

Meta.db
-------

It's important that each ``Table`` class knows which engine to use. This is set
via the ``Meta.db`` attribute. There are two ways of doing this - setting it
explicitly, or using ``engine_finder``.

Explicit
--------

.. code-block:: python

    from piccolo.engine.sqlite import SQLiteEngine
    from piccolo.tables import Table
    from piccolo.columns import Varchar


    DB = SQLiteEngine(path='my_db.sqlite')


    class MyTable(Table):
        name = Varchar()

        class Meta:
            # Here we explicitly reference an engine
            db = DB


engine_finder
-------------

By using ``engine_finder``, Piccolo will look for a file called
``piccolo_conf.py`` on the path, and will try and import a ``DB`` variable,
which defines the engine. This is the default behavior, if no ``Meta`` class is
defined.

.. code-block:: python

    from piccolo.engine.finder import engine_finder
    from piccolo.tables import Table
    from piccolo.columns import Varchar


    class MyTable(Table):
        name = Varchar()

        class Meta:
            # Let Piccolo import the engine from a config file:
            db = engine_finder()

Here's an example config file:

.. code-block:: python

    # piccolo_conf.py
    from piccolo.engine.sqlite import SQLiteEngine


    DB = SQLiteEngine(path='my_db.sqlite')

.. hint:: Put your config files at the root of your project, where the
    Python interpreter will be launched.

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
