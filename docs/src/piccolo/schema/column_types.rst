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

====================
``JSON`` / ``JSONB``
====================

.. autoclass:: JSON

.. autoclass:: JSONB

===========
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

=============
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

================
Getting elements
================

``JSON`` and ``JSONB`` columns have an ``arrow`` method (representing the
``->`` operator in Postgres), which is useful for retrieving a child element
from the JSON data.

.. note:: Postgres and CockroachDB only.

``select`` queries
==================

If we have the following JSON stored in the ``RecordingStudio.facilities``
column:

.. code-block:: json

    {
        "instruments": {
            "drum_kits": 2,
            "electric_guitars": 10
        },
        "restaurant": true,
        "technicians": [
            {
                "name": "Alice Jones"
            },
            {
                "name": "Bob Williams"
            }
        ]
    }

We can retrieve the ``restaurant`` value from the JSON object:

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities.arrow('restaurant')
    ...     .as_alias('restaurant')
    ... ).output(load_json=True)
    [{'restaurant': True}, ...]

As a convenience, you can use square brackets, instead of calling ``arrow``
explicitly:

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities['restaurant']
    ...     .as_alias('restaurant')
    ... ).output(load_json=True)
    [{'restaurant': True}, ...]

You can drill multiple levels deep by calling ``arrow`` multiple times (or
alternatively use the :ref:`from_path` method - see below).

Here we fetch the number of drum kits that the recording studio has:

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities["instruments"]["drum_kits"]
    ...     .as_alias("drum_kits")
    ... ).output(load_json=True)
    [{'drum_kits': 2}, ...]

If you have a JSON object which consists of arrays and objects, then you can
navigate the array elements by passing in an integer to ``arrow``.

Here we fetch the first technician from the array:

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities["technicians"][0]["name"]
    ...     .as_alias("technician_name")
    ... ).output(load_json=True)

    [{'technician_name': 'Alice Jones'}, ...]

``where`` clauses
=================

The ``arrow`` operator can also be used for filtering in a where clause:

.. code-block:: python

    >>> await RecordingStudio.select(RecordingStudio.name).where(
    ...     RecordingStudio.facilities['mixing_desk'].eq(True)
    ... )
    [{'name': 'Abbey Road'}]

.. _from_path:

=============
``from_path``
=============

This works the same as ``arrow`` but is more optimised if you need to return
part of a highly nested JSON structure.

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities.from_path([
    ...         "technicians",
    ...         0,
    ...         "name"
    ...     ]).as_alias("technician_name")
    ... ).output(load_json=True)

    [{'technician_name': 'Alice Jones'}, ...]

=============
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

=======
not_any
=======

.. automethod:: Array.not_any

===
all
===

.. automethod:: Array.all

===
cat
===

.. automethod:: Array.cat

======
remove
======

.. automethod:: Array.remove

======
append
======

.. automethod:: Array.append


=======
prepend
=======

.. automethod:: Array.prepend

=======
replace
=======

.. automethod:: Array.replace
