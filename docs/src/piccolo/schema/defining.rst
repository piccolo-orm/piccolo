.. _DefiningSchema:

Defining a Schema
=================

The schema is usually defined within the ``tables.py`` file of your
:ref:`Piccolo app <PiccoloApps>`.

This reflects the tables in your database. Each table consists of several
columns. Here's a very simple schema:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import Varchar


    class Band(Table):
        name = Varchar(length=100)

For a full list of columns, see :ref:`column types <ColumnTypes>`.

.. hint:: If you're using an existing database, see Piccolo's
 :ref:`auto schema generation command<SchemaApp>`, which will save you some
 time.

-------------------------------------------------------------------------------

Primary Key
-----------

Piccolo tables are automatically given a primary key column called ``id``,
which is an auto incrementing integer (a ``Serial(primary_key=True)`` column).

There is currently experimental support for specifying a custom primary key
column. For example:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import UUID, Varchar


    class Band(Table):
        id = UUID(primary_key=True)
        name = Varchar(length=100)

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
