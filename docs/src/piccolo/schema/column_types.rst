.. _ColumnTypes:

.. currentmodule:: piccolo.columns.column_types

############
Column Types
############

.. hint:: You'll notice that the column names tend to match their SQL
    equivalents.

******
Column
******

.. autoclass:: Column

-------------------------------------------------------------------------------

*****
Bytea
*****

.. autoclass:: Bytea

.. hint:: There is also a ``Blob`` column type, which is an alias for
    ``Bytea``.

-------------------------------------------------------------------------------

*******
Boolean
*******

.. autoclass:: Boolean

-------------------------------------------------------------------------------

**********
ForeignKey
**********

.. autoclass:: ForeignKey

-------------------------------------------------------------------------------

******
Number
******

======
BigInt
======

.. autoclass:: BigInt

=======
Integer
=======

.. autoclass:: Integer

=======
Numeric
=======

.. autoclass:: Numeric

.. hint:: There is also a ``Decimal`` column type, which is an alias for
    ``Numeric``.

====
Real
====

.. autoclass:: Real

.. hint:: There is also a ``Float`` column type, which is an alias for
    ``Real``.


================
Double Precision
================

.. autoclass:: DoublePrecision

========
SmallInt
========

.. autoclass:: SmallInt

-------------------------------------------------------------------------------

****
UUID
****

.. autoclass:: UUID

-------------------------------------------------------------------------------

****
Text
****

======
Secret
======

.. autoclass:: Secret

====
Text
====

.. autoclass:: Text

=======
Varchar
=======

.. autoclass:: Varchar

-------------------------------------------------------------------------------

****
Time
****

====
Date
====

.. autoclass:: Date

========
Interval
========

.. autoclass:: Interval

====
Time
====

.. autoclass:: Time

=========
Timestamp
=========

.. autoclass:: Timestamp

===========
Timestamptz
===========

.. autoclass:: Timestamptz

-------------------------------------------------------------------------------

****
JSON
****

Storing JSON can be useful in certain situations, for example - raw API
responses, data from a Javascript app, and for storing data with an unknown or
changing schema.

====
JSON
====

.. autoclass:: JSON

=====
JSONB
=====

.. autoclass:: JSONB

arrow
=====

``JSONB`` columns have an ``arrow`` function, which is useful for retrieving
a subset of the JSON data, and for filtering in a where clause.

.. code-block:: python

    # Example schema:
    class Booking(Table):
        data = JSONB()

    Booking.create_table().run_sync()

    # Example data:
    Booking.insert(
        Booking(data='{"name": "Alison"}'),
        Booking(data='{"name": "Bob"}')
    ).run_sync()

    # Example queries
    >>> Booking.select(
    >>>     Booking.id, Booking.data.arrow('name').as_alias('name')
    >>> ).run_sync()
    [{'id': 1, 'name': '"Alison"'}, {'id': 2, 'name': '"Bob"'}]

    >>> Booking.select(Booking.id).where(
    >>>     Booking.data.arrow('name') == '"Alison"'
    >>> ).run_sync()
    [{'id': 1}]

-------------------------------------------------------------------------------

*****
Array
*****

Arrays of data can be stored, which can be useful when you want store lots of
values without using foreign keys.

.. autoclass:: Array

=============================
Accessing individual elements
=============================

.. automethod:: Array.__getitem__

===
any
===

.. automethod:: Array.any

===
all
===

.. automethod:: Array.all
