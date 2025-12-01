MySQLEngine
===========

Configuration
-------------

.. code-block:: python

    # piccolo_conf.py
    from piccolo.engine.mysql import MySQLEngine


    DB = MySQLEngine(
        config={
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "db": "piccolo",
        }
    )

config
~~~~~~

The config dictionary is passed directly to the underlying 
database adapter, aiomysql. See the `aiomysql docs <https://aiomysql.readthedocs.io/en/stable/connection.html#connection>`_
to learn more.

-------------------------------------------------------------------------------

Connection pool
---------------

To use a connection pool, you need to first initialise it. The best place to do
this is in the startup event handler of whichever web framework you are using.

Here's an example using Starlette. Notice that we also close the connection
pool in the shutdown event handler.

.. code-block:: python

    from piccolo.engine import engine_finder
    from starlette.applications import Starlette


    app = Starlette()


    @app.on_event('startup')
    async def open_database_connection_pool():
        engine = engine_finder()
        await engine.start_connection_pool()


    @app.on_event('shutdown')
    async def close_database_connection_pool():
        engine = engine_finder()
        await engine.close_connection_pool()

.. hint:: Using a connection pool helps with performance, since connections
    are reused instead of being created for each query.

Once a connection pool has been started, the engine will use it for making
queries.

Configuration
~~~~~~~~~~~~~

The connection pool uses the same configuration as your engine. You can also
pass in additional parameters, which are passed to the underlying database
adapter. Here's an example:

.. code-block:: python

    # To increase the number of connections available:
    await engine.start_connection_pool(max_size=20)

-------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.engine.mysql

.. autoclass:: MySQLEngine
