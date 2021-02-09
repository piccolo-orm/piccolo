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
