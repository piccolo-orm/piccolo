SQLiteEngine
============

Configuration
-------------

The ``SQLiteEngine`` is very simple - just specify a file path. The database
file will be created automatically if it doesn't exist.

.. code-block:: python

    # piccolo_conf.py
    from piccolo.engine.sqlite import SQLiteEngine


    DB = SQLiteEngine(path='my_app.sqlite')

-------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.engine.sqlite

.. autoclass:: SQLiteEngine

-------------------------------------------------------------------------------

Production tips
---------------

If you're planning on using SQLite in production with Piccolo, with lots of
concurrent queries, then here are some :ref:`useful tips <UsingSQLiteAndAsyncioEffectively>`.
