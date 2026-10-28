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

UUID
~~~~

To specify a :class:`UUID <piccolo.columns.column_types.UUID>` primary key
column, do the following:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import UUID, Varchar


    class Band(Table):
        id = UUID(primary_key=True)
        name = Varchar(length=100)

Identity
~~~~~~~~

To specify an :ref:`identity column<IdentityColumns>` as the primary key,
do the following:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import BigInt, Varchar
    from piccolo.columns.generated import Identity


    class Band(Table):
        id = BigInt(primary_key=True, generated=Identity())
        name = Varchar(length=100)

.. hint::
    This is the recommended alternative to ``Serial`` in Postgres.

Serial / BigSerial
~~~~~~~~~~~~~~~~~~

To specify a :class:`Serial <piccolo.columns.column_types.Serial>` /
:class:`BigSerial <piccolo.columns.column_types.BigSerial>` column as the
primary key, do the following:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import BigSerial, Varchar


    class Band(Table):
        id = BigSerial(primary_key=True)
        name = Varchar(length=100)

.. hint::
    Even though identity columns are recommended instead of
    ``Serial`` / ``BigSerial`` for Postgres, these still work fine - the differences are
    fairly minor.

Default
~~~~~~~

If no primary key is specified, then Piccolo tables are automatically given one
called ``id``, which is an auto incrementing integer
(a ``Serial(primary_key=True)`` column).

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
