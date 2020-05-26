.. _ColumnTypes:

Column Types
============

.. hint:: You'll notice that the column names tend to match their SQL
    equivalents.

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

Secret
------

The database treats it the same as a Varchar, but Piccolo may treat it
differently internally - for example, allowing a user to automatically omit any
secret fields when doing a select query, to help prevent inadvertant leakage.
A common use for a Secret field is a password.

.. code-block:: python

    class Band(Table):
        password = Secret(length=100)

Numeric
-------

Used for storing decimal numbers, when precision is important. An example
use case is storing financial data.

When creating the column, you specify how many digits are allowed using a
tuple. The first value is the `precision`, which is the total number of digits
allowed. The second value is the `range`, which specifies how many of those
digits are after the decimal point. For example, to store monetary values up
to £999.99, the digits argument is `(5,2)`.

.. code-block:: python

    class Ticket(Table):
        price = Numeric(digits=(5,2))

Piccolo uses Python `Decimal` numbers to represent numeric values.

.. code-block:: python

    from decimal import Decimal

    ticket = Ticket(price=Decimal('50.0'))

.. hint:: There is also a Decimal column type, which is an alias for Numeric.


Real
----

Used for storing numbers, when the precision isn't important.

.. code-block:: python

    class Concert(Table):
        rating = Real()

Piccolo uses floats to represent real values.

.. code-block:: python

    concert = Concert(rating=7.8)

.. hint:: There is also a Float column type, which is an alias for Real.
