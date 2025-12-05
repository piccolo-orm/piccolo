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

connection pool
~~~~~~~~~~~~~~~

.. toctree::
    :maxdepth: 1

    ./connection_pool

-------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.engine.postgres

.. autoclass:: PostgresEngine
