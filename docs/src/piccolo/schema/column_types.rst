.. _ColumnTypes:

Column Types
============

.. hint:: You'll notice that all of the column names match their SQL equivalents.

Column
------

All other columns inherit from ``Column``. Don't use it directly.

The following arguments apply to all column types:

default
~~~~~~~

.. code-block:: python

    class Band(Table):
        name = Varchar(default="hello")

null
~~~~

Whether the column is nullable.

.. code-block:: python

    class Band(Table):
        name = Varchar(default="hello", null=False)

Varchar
-------

Use when you want to impose a limit to string size.

.. code-block:: python

    class Band(Table):
        name = Varchar(length=100)

Text
----

Use when you want to don't want to limit string size.

.. code-block:: python

    class Band(Table):
        name = Text()

ForeignKey
----------

`ForeignKey` takes a `Table` argument.

.. code-block:: python

    class Band(Table):
        manager = ForeignKey(Manager)

A table can have a reference to itself, if you pass a table argument of 'self'.

.. code-block:: python

    class Employee(Table):
        name = Varchar(max_length=100)
        manager = ForeignKey('self')

Integer
-------

.. code-block:: python

    class Band(Table):
        popularity = Integer()

BigInt
------

In Postgres, this column supports large integers. In SQLite, it's an alias to
an Integer column, which already supports large integers.

.. code-block:: python

    class Band(Table):
        value = BigInt()


SmallInt
--------

In Postgres, this column supports small integers. In SQLite, it's an alias to
an Integer column.

.. code-block:: python

    class Band(Table):
        value = SmallInt()


Timestamp
---------

.. code-block:: python

    class Band(Table):
        created = Timestamp()

Boolean
-------

.. code-block:: python

    class Band(Table):
        has_drummer = Boolean()

UUID
----

.. code-block:: python

    class Band(Table):
        uuid = UUID()
