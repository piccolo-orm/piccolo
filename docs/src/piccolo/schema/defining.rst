.. _DefiningSchema:

Defining a Schema
=================

The first step is to define your schema. Create a file called ``tables.py``.

This reflects the tables in your database. Each table consists of several
columns.

.. code-block:: python

    """
    tables.py
    """
    from piccolo.tables import Table
    from piccolo.columns import Varchar


    class Band(Table):
        name = Varchar(length=100)

For a full list of columns, see :ref:`ColumnTypes`.

Connecting to the database
--------------------------

In order to create the table and query the database, you need to provide
Piccolo with your connection details. See :ref:`Engines`.
