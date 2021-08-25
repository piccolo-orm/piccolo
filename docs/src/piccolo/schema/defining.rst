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

.. hint:: If you're using an existing database, see Piccolo's
 :ref:`auto schema generation command<SchemaApp>`, which will save you some
 time.

-------------------------------------------------------------------------------

Primary Key
---------------

You can specify your ``PrimaryKey`` with any column type by passing ``primary_key`` to the ``Column``.

It is used to uniquely identify a row, and is referenced by ``ForeignKey``
columns on other tables.

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import UUID, Varchar


    class Band(Table):
        id = UUID(primary_key=True)
        name = Varchar(length=100)

If you don't specify a ``PrimaryKey``, the table is automatically given a ``PrimaryKey`` column called ``id``, which
is an auto incrementing integer.

This is equivalent to:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import Serial, Varchar


    class Band(Table):
        id = Serial(primary_key=True)
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
