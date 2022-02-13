.. _Select:

Select
======

.. hint:: Follow along by installing Piccolo and running ``piccolo playground run`` - see :ref:`Playground`.

To get all rows:

.. code-block:: python

    >>> await Band.select()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

To get certain columns:

.. code-block:: python

    >>> await Band.select(Band.name)
    [{'name': 'Rustaceans'}, {'name': 'Pythonistas'}]

Or use an alias to make it shorter:

.. code-block:: python

    >>> b = Band
    >>> await b.select(b.name)
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

.. hint::
   All of these examples also work synchronously using ``run_sync`` -
   see :ref:`SyncAndAsync`.

-------------------------------------------------------------------------------

as_alias
--------

By using ``as_alias``, the name of the row can be overriden in the response.

.. code-block:: python

    >>> await Band.select(Band.name.as_alias('title'))
    [{'title': 'Rustaceans'}, {'title': 'Pythonistas'}]

This is equivalent to ``SELECT name AS title FROM band`` in SQL.

-------------------------------------------------------------------------------

Joins
-----

One of the most powerful things about ``select`` is it's support for joins.

.. code-block:: python

    >>> await Band.select(Band.name, Band.manager.name)
    [
        {'name': 'Pythonistas', 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.name': 'Graydon'}
    ]


The joins can go several layers deep.

.. code-block:: python

    >>> await Concert.select(Concert.id, Concert.band_1.manager.name)
    [{'id': 1, 'band_1.manager.name': 'Guido'}]

all_columns
~~~~~~~~~~~

If you want all of the columns from a related table you can use
``all_columns``, which is a useful shortcut which saves you from typing them
all out:

.. code-block:: python

    >>> await Band.select(Band.name, Band.manager.all_columns())
    [
        {'name': 'Pythonistas', 'manager.id': 1, 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.id': 2, 'manager.name': 'Graydon'}
    ]


In Piccolo < 0.41.0 you had to explicitly unpack ``all_columns``. This is
equivalent to the code above:

.. code-block:: python

    >>> await Band.select(Band.name, *Band.manager.all_columns())


You can exclude some columns if you like:

.. code-block:: python

    >>> await Band.select(
    >>>     Band.name,
    >>>     Band.manager.all_columns(exclude=[Band.manager.id])
    >>> )
    [
        {'name': 'Pythonistas', 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.name': 'Graydon'}
    ]


Strings are supported too if you prefer:

.. code-block:: python

    >>> await Band.select(
    >>>     Band.name,
    >>>     Band.manager.all_columns(exclude=['id'])
    >>> )
    [
        {'name': 'Pythonistas', 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.name': 'Graydon'}
    ]

You can also use ``all_columns`` on the root table, which saves you time if
you have lots of columns. It works identically to related tables:

.. code-block:: python

    >>> await Band.select(
    >>>     Band.all_columns(exclude=[Band.id]),
    >>>     Band.manager.all_columns(exclude=[Band.manager.id])
    >>> )
    [
        {'name': 'Pythonistas', 'popularity': 1000, 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'popularity': 500, 'manager.name': 'Graydon'}
    ]

Nested
~~~~~~

You can also get the response as nested dictionaries, which can be very useful:

.. code-block:: python

    >>> await Band.select(Band.name, Band.manager.all_columns()).output(nested=True)
    [
        {'name': 'Pythonistas', 'manager': {'id': 1, 'name': 'Guido'}},
        {'name': 'Rustaceans', 'manager': {'id': 2, 'manager.name': 'Graydon'}}
    ]

-------------------------------------------------------------------------------

String syntax
-------------

You can specify the column names using a string if you prefer. The
disadvantage is you won't have tab completion, but sometimes it's more
convenient.

.. code-block:: python

    await Band.select('name')

    # For joins:
    await Band.select('manager.name')

-------------------------------------------------------------------------------

Aggregate functions
-------------------

Count
~~~~~

Returns the number of rows which match the query:

.. code-block:: python

    >>> await Band.count().where(Band.name == 'Pythonistas')
    1

Avg
~~~

Returns the average for a given column:

.. code-block:: python

    >>> from piccolo.query import Avg
    >>> response = await Band.select(Avg(Band.popularity)).first()
    >>> response["avg"]
    750.0

Sum
~~~

Returns the sum for a given column:

.. code-block:: python

    >>> from piccolo.query import Sum
    >>> response = await Band.select(Sum(Band.popularity)).first()
    >>> response["sum"]
    1500

Max
~~~

Returns the maximum for a given column:

.. code-block:: python

    >>> from piccolo.query import Max
    >>> response = await Band.select(Max(Band.popularity)).first()
    >>> response["max"]
    1000

Min
~~~

Returns the minimum for a given column:

.. code-block:: python

    >>> from piccolo.query import Min
    >>> response = await Band.select(Min(Band.popularity)).first()
    >>> response["min"]
    500

Additional features
~~~~~~~~~~~~~~~~~~~

You also can have multiple different aggregate functions in one query:

.. code-block:: python

    >>> from piccolo.query import Avg, Sum
    >>> response = await Band.select(Avg(Band.popularity), Sum(Band.popularity)).first()
    >>> response
    {"avg": 750.0, "sum": 1500}

And can use aliases for aggregate functions like this:

.. code-block:: python

    # Alternatively, you can use the `as_alias` method.
    >>> response = await Band.select(Avg(Band.popularity).as_alias("popularity_avg")).first()
    >>> response["popularity_avg"]
    750.0

-------------------------------------------------------------------------------

Query clauses
-------------

batch
~~~~~

See :ref:`batch`.

columns
~~~~~~~

By default all columns are returned from the queried table.

.. code-block:: python

    # Equivalent to SELECT * from band
    await Band.select()

To restrict the returned columns, either pass in the columns into the
``select`` method, or use the ``columns`` method.

.. code-block:: python

    # Equivalent to SELECT name from band
    await Band.select(Band.name)

    # Or alternatively:
    await Band.select().columns(Band.name)

The ``columns`` method is additive, meaning you can chain it to add additional
columns.

.. code-block:: python

    await Band.select().columns(Band.name).columns(Band.manager)

    # Or just define it one go:
    await Band.select().columns(Band.name, Band.manager)


first
~~~~~

See :ref:`first`.

group_by
~~~~~~~~

See :ref:`group_by`.

limit
~~~~~

See :ref:`limit`.

offset
~~~~~~

See :ref:`offset`.

distinct
~~~~~~~~

See :ref:`distinct`.

order_by
~~~~~~~~

See :ref:`order_by`.

output
~~~~~~

See :ref:`output`.

where
~~~~~

See :ref:`where`.
