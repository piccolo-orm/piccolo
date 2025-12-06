CockroachEngine
===============

Configuration
-------------

.. code-block:: python

    # piccolo_conf.py
    from piccolo.engine.cockroach import CockroachEngine


    DB = CockroachEngine(config={
        'host': 'localhost',
        'database': 'piccolo',
        'user': 'root',
        'password': '',
        'port': '26257',
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

.. currentmodule:: piccolo.engine.cockroach

.. autoclass:: CockroachEngine
