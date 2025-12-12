.. _ConnectionPool:

Connection Pool
===============

.. hint:: Connection pools can be used with Postgres, CockroachDB and MySQL.

Setup
~~~~~

To use a connection pool, you need to first initialise it. The best place to do
this is in the startup event handler of whichever web framework you are using.
We also want to close the connection pool in the shutdown event handler.

The recommended way for Starlette and FastAPI apps is to use the ``lifespan``
parameter:

.. code-block:: python

    from contextlib import asynccontextmanager
    from piccolo.engine import engine_finder
    from starlette.applications import Starlette


    @asynccontextmanager
    async def lifespan(app: Starlette):
        engine = engine_finder()
        assert engine
        await engine.start_connection_pool()
        yield
        await engine.close_connection_pool()


    app = Starlette(lifespan=lifespan)

In older versions of Starlette and FastAPI, you may need event handlers
instead:

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

.. hint:: If you're running several instances of an app on the same server,
    you may prefer an external connection pooler - like pgbouncer.

-------------------------------------------------------------------------------

Configuration
~~~~~~~~~~~~~

The connection pool uses the same configuration as your engine. You can also
pass in additional parameters, which are passed to the underlying database
adapter. Here's an example:

.. code-block:: python

    # To increase the number of connections available:
    await engine.start_connection_pool(max_size=20)