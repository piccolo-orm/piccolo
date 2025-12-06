PostgresEngine
==============

Configuration
-------------

.. code-block:: python

    # piccolo_conf.py
    from piccolo.engine.postgres import PostgresEngine


    DB = PostgresEngine(config={
        'host': 'localhost',
        'database': 'my_app',
        'user': 'postgres',
        'password': ''
    })

config
~~~~~~

The config dictionary is passed directly to the underlying database adapter,
asyncpg. See the `asyncpg docs <https://magicstack.github.io/asyncpg/current/api/index.html#connection>`_
to learn more.

-------------------------------------------------------------------------------

Connection Pool
---------------

See :ref:`ConnectionPool`.

-------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.engine.postgres

.. autoclass:: PostgresEngine
