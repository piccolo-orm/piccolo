.. _ColumnTypes:

############
Column Types
############

.. hint:: You'll notice that the column names tend to match their SQL
    equivalents.

******
Column
******

.. currentmodule:: piccolo.columns.base

.. autoclass:: Column
    :noindex:

-------------------------------------------------------------------------------

*****
Bytea
*****

.. currentmodule:: piccolo.columns.column_types

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

=========
BigSerial
=========

.. autoclass:: BigSerial

================
Double Precision
================

.. autoclass:: DoublePrecision

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

======
Serial
======

.. autoclass:: Serial

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

=====
Email
=====

.. autoclass:: Email

--------------------------------------------------------------------------

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

Serialising
===========

Piccolo automatically converts Python values into JSON strings:

.. code-block:: python

    studio = RecordingStudio(
        name="Abbey Road",
        facilities={"restaurant": True, "mixing_desk": True}  # Automatically serialised
    )
    await studio.save()

You can also pass in a JSON string if you prefer:

.. code-block:: python

    studio = RecordingStudio(
        name="Abbey Road",
        facilities='{"restaurant": true, "mixing_desk": true}'
    )
    await studio.save()

Deserialising
=============

The contents of a ``JSON`` / ``JSONB`` column are returned as a string by
default:

.. code-block:: python

    >>> await RecordingStudio.select(RecordingStudio.facilities)
    [{facilities: '{"restaurant": true, "mixing_desk": true}'}]

However, we can ask Piccolo to deserialise the JSON automatically (see :ref:`load_json`):

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities
    ... ).output(
    ...     load_json=True
    ... )
    [facilities: {"restaurant": True, "mixing_desk": True}}]

With ``objects`` queries, we can modify the returned JSON, and then save it:

.. code-block:: python

    studio = await RecordingStudio.objects().get(
        RecordingStudio.name == 'Abbey Road'
    ).output(load_json=True)

    studio['facilities']['restaurant'] = False
    await studio.save()

arrow
=====

``JSONB`` columns have an ``arrow`` function, which is useful for retrieving
a subset of the JSON data:

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.name,
    ...     RecordingStudio.facilities.arrow('mixing_desk').as_alias('mixing_desk')
    ... ).output(load_json=True)
    [{'name': 'Abbey Road', 'mixing_desk': True}]

It can also be used for filtering in a where clause:

.. code-block:: python

    >>> await RecordingStudio.select(RecordingStudio.name).where(
    ...     RecordingStudio.facilities.arrow('mixing_desk') == True
    ... )
    [{'name': 'Abbey Road'}]

Handling null
=============

When assigning a value of ``None`` to a ``JSON`` or ``JSONB`` column, this is
treated as null in the database.

.. code-block:: python

    await RecordingStudio(name="ABC Studios", facilities=None).save()

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities
    ... ).where(
    ...     RecordingStudio.name == "ABC Studios"
    ... )
    [{'facilities': None}]


If instead you want to store JSON null in the database, assign a value of ``'null'``
instead.

.. code-block:: python

    await RecordingStudio(name="ABC Studios", facilities='null').save()

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities
    ... ).where(
    ...     RecordingStudio.name == "ABC Studios"
    ... )
    [{'facilities': 'null'}]

-------------------------------------------------------------------------------

*****
Array
*****

Arrays of data can be stored, which can be useful when you want to store lots
of values without using foreign keys.

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

===
cat
===

.. automethod:: Array.cat
