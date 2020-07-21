.. _DefiningSchema:

Defining a Schema
=================

The schema is usually defined within the ``tables.py`` file of your Piccolo
app (see :ref:`PiccoloApps`).

This reflects the tables in your database. Each table consists of several
columns. Here's a very simple schema:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import Varchar


    class Band(Table):
        name = Varchar(length=100)

For a full list of columns, see :ref:`ColumnTypes`.

-------------------------------------------------------------------------------

Tablename
---------

By default, the name of the table in the database is the Python class name,
converted to snakecase. For example ``Band -> band``, and
``MusicAward -> music_award``.

You can specify a custom tablename to use instead.

.. code-block:: python

    class Band(Table, tablename="music_band"):
        name = Varchar(length=100)

-------------------------------------------------------------------------------

Connecting to the database
--------------------------

In order to create the table and query the database, you need to provide
Piccolo with your connection details. See :ref:`Engines`.
