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

The config dictionary is passed directly to the underlying database adapter, 
aiomysql. See the `aiomysql docs <https://aiomysql.readthedocs.io/en/stable/connection.html#connection>`_
to learn more.

-------------------------------------------------------------------------------

Connection Pool
---------------

See :ref:`ConnectionPool`.

-------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.engine.mysql

.. autoclass:: MySQLEngine
