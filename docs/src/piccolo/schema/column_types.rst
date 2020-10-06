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
