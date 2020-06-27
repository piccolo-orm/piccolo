.. _ColumnTypes:

############
Column Types
############

.. hint:: You'll notice that the column names tend to match their SQL
    equivalents.

******
Column
******

All other columns inherit from ``Column``. Don't use it directly.

Args
====

The following arguments apply to all column types:

default
-------

The column value to use if not specified by the user.

.. code-block:: python

    class Band(Table):
        name = Varchar(default='hello')

null
----

Whether the column is nullable.

 * type: ``bool``
 * default: ``True``

.. code-block:: python

    class Band(Table):
        name = Varchar(default='hello', null=False)

-------------------------------------------------------------------------------

*******
Varchar
*******

Use when you want to store strings, and need to impose a limit to the length.

Args
====

length
------

The maximum number of characters allowed.

 * type: ``int``
 * default: ``255``

Example
=======

.. code-block:: python

    class Band(Table):
        name = Varchar(length=100)

Type
====

``Varchar`` uses the ``str`` type for values.

.. code-block:: python

    # Create
    >>> Band(name='Pythonistas').save().run_sync()

    # Query
    >>> Band.select(Band.name).run_sync()
    {'name': 'Pythonistas'}

-------------------------------------------------------------------------------

****
Text
****

Use when you want to store large strings, and don't want to limit the string
size.

Example
=======

.. code-block:: python

    class Band(Table):
        name = Text()

Type
====

``Text`` uses the ``str`` type for values.

.. code-block:: python

    # Create
    >>> Band(name='Pythonistas').save().run_sync()

    # Query
    >>> Band.select(Band.name).run_sync()
    {'name': 'Pythonistas'}

-------------------------------------------------------------------------------

**********
ForeignKey
**********

Used to reference another table.

Args
====

references
----------

The ``Table`` being referenced.

 * type: ``Table`` or ``str``
 * required

A table can have a reference to itself, if you pass a ``references`` argument
of ``'self'``.

.. code-block:: python

    class Musician(Table):
        name = Varchar(length=100)
        instructor = ForeignKey(references='self')

on_delete
---------

Determines what the database should do when a row is deleted with foreign keys
referencing it. If set to ``OnDelete.cascade``, any rows referencing the
deleted row are also deleted.

 * type: ``OnDelete``
 * default: ``OnDelete.cascade``
 * options: ``OnDelete.cascade``, ``OnDelete.restrict``, ``OnDelete.no_action``,  ``OnDelete.set_null``, ``OnDelete.set_default``

To learn more about the different options, see the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK>`_.

.. code-block:: python

    from piccolo.columns import OnDelete

    class Band(Table):
        name = ForeignKey(references=Manager, on_delete=OnDelete.cascade)

on_update
---------

Determines what the database should do when a row has it's primary key updated.
If set to ``OnDelete.cascade``, any rows referencing the updated row will
have their references updated to point to the new primary key.

 * type: ``OnUpdate``
 * default: ``OnUpdate.cascade``
 * options: ``OnUpdate.cascade``, ``OnUpdate.restrict``, ``OnUpdate.no_action``, ``OnUpdate.set_null``, ``OnUpdate.set_default``

To learn more about the different options, see the `Postgres docs <https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK>`_.

.. code-block:: python

    from piccolo.columns import OnDelete

    class Band(Table):
        name = ForeignKey(references=Manager, on_update=OnUpdate.cascade)

Example
=======

.. code-block:: python

    class Band(Table):
        manager = ForeignKey(references=Manager)

Type
====

``ForeignKey`` uses the ``int`` type for values.

.. code-block:: python

    # Create
    >>> Band(manager=1).save().run_sync()

    # Query
    >>> Band.select(Band.manager).run_sync()
    {'manager': 1}

-------------------------------------------------------------------------------

*******
Integer
*******

Used for storing whole numbers.

Example
=======

.. code-block:: python

    class Band(Table):
        popularity = Integer()

Type
====

``Integer`` uses the ``int`` type for values.

.. code-block:: python

    # Create
    >>> Band(popularity=1000).save().run_sync()

    # Query
    >>> Band.select(Band.popularity).run_sync()
    {'popularity': 1000}

-------------------------------------------------------------------------------

******
BigInt
******

In Postgres, this column supports large integers. In SQLite, it's an alias to
an Integer column, which already supports large integers.

Example
=======

.. code-block:: python

    class Band(Table):
        value = BigInt()

Type
====

``BigInt`` uses the ``int`` type for values.

.. code-block:: python

    # Create
    >>> Band(popularity=1000000).save().run_sync()

    # Query
    >>> Band.select(Band.popularity).run_sync()
    {'popularity': 1000000}

-------------------------------------------------------------------------------

********
SmallInt
********

In Postgres, this column supports small integers. In SQLite, it's an alias to
an Integer column.

Example
=======

.. code-block:: python

    class Band(Table):
        value = SmallInt()

Type
====

``SmallInt`` uses the ``int`` type for values.

.. code-block:: python

    # Create
    >>> Band(popularity=1000).save().run_sync()

    # Query
    >>> Band.select(Band.popularity).run_sync()
    {'popularity': 1000}

-------------------------------------------------------------------------------

*********
Timestamp
*********

Used for storing datetimes.

Example
=======

.. code-block:: python

    class Concert(Table):
        starts = Timestamp()

It's common to want a default for a timestamp column. Having functions as
defaults can cause issues for migrations, so the recommended way to have
a default of `now` is as follows:

.. code-block:: python

    from piccolo.custom_types import TimestampDefault


    class Concert(Table):
        starts = Timestamp(default=TimestampDefault.now)


Type
====

``Timestamp`` uses the ``datetime`` type for values.

.. code-block:: python

    import datetime

    # Create
    >>> Concert(starts=datetime.datetime(year=2050, month=1, day=1)).save().run_sync()

    # Query
    >>> Concert.select(Concert.starts).run_sync()
    {'starts': datetime.datetime(2050, 1, 1, 0, 0)}

-------------------------------------------------------------------------------

*******
Boolean
*******

Used for storing True / False values.

Example
=======

.. code-block:: python

    class Band(Table):
        has_drummer = Boolean()

Type
====

``Boolean`` uses the ``bool`` type for values.

.. code-block:: python

    # Create
    >>> Band(has_drummer=True).save().run_sync()

    # Query
    >>> Band.select(Band.has_drummer).run_sync()
    {'has_drummer': True}

-------------------------------------------------------------------------------

****
UUID
****

Used for storing UUIDs - in Postgres a UUID column type is used, and in SQLite
it's just a Varchar.

Example
=======

.. code-block:: python

    class Band(Table):
        uuid = UUID()

Type
====

``UUID`` uses the ``UUID`` type for values.

.. code-block:: python

    import uuid

    # Create
    >>> DiscountCode(code=uuid.uuid4()).save().run_sync()

    # Query
    >>> DiscountCode.select(DiscountCode.code).run_sync()
    {'code': UUID('09c4c17d-af68-4ce7-9955-73dcd892e462')}

-------------------------------------------------------------------------------

******
Secret
******

The database treats it the same as a Varchar, but Piccolo may treat it
differently internally - for example, allowing a user to automatically omit any
secret fields when doing a select query, to help prevent inadvertant leakage.
A common use for a Secret field is a password.

Example
=======

.. code-block:: python

    class Door(Table):
        code = Secret(length=100)

Type
====

``Secret`` uses the ``str`` type for values.

.. code-block:: python

    # Create
    >>> Door(code='123abc').save().run_sync()

    # Query
    >>> Door.select(Door.code).run_sync()
    {'code': '123abc'}

-------------------------------------------------------------------------------

*******
Numeric
*******

Used for storing decimal numbers, when precision is important. An example
use case is storing financial data.

Args
====

digits
------

When creating the column, you specify how many digits are allowed using a
tuple. The first value is the `precision`, which is the total number of digits
allowed. The second value is the `range`, which specifies how many of those
digits are after the decimal point. For example, to store monetary values up
to £999.99, the digits argument is `(5,2)`.

 * type: ``tuple``
 * required

Example
=======

.. code-block:: python

    class Ticket(Table):
        price = Numeric(digits=(5,2))

Type
====

``Numeric`` uses the ``Decimal`` type for values.

.. code-block:: python

    from decimal import Decimal

    # Create
    >>> Ticket(price=Decimal('50.0')).save().run_sync()

    # Query
    >>> Ticket.select(Ticket.price).run_sync()
    {'price': Decimal('50.0')}

.. hint:: There is also a Decimal column type, which is an alias for Numeric.

-------------------------------------------------------------------------------

****
Real
****

Used for storing numbers, when the precision isn't important.

Example
=======

.. code-block:: python

    class Concert(Table):
        rating = Real()

Type
====

``Real`` uses the ``float`` type for values.

.. code-block:: python

    # Create
    >>> Concert(rating=7.8).save().run_sync()

    # Query
    >>> Concert.select(Concert.rating).run_sync()
    {'rating': 7.8}


.. hint:: There is also a Float column type, which is an alias for Real.
