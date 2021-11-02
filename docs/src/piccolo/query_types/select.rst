.. _Select:

Select
======

.. hint:: Follow along by installing Piccolo and running ``piccolo playground run`` - see :ref:`Playground`

To get all rows:

.. code-block:: python

    >>> Band.select().run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

To get certain columns:

.. code-block:: python

    >>> Band.select(Band.name).run_sync()
    [{'name': 'Rustaceans'}, {'name': 'Pythonistas'}]

Or use an alias to make it shorter:

.. code-block:: python

    >>> b = Band
    >>> b.select(b.name).run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

.. hint:: All of these examples also work with async by using .run() inside coroutines - see :ref:`SyncAndAsync`.

-------------------------------------------------------------------------------

as_alias
--------

By using ``as_alias``, the name of the row can be overriden in the response.

.. code-block:: python

    >>> Band.select(Band.name.as_alias('title')).run_sync()
    [{'title': 'Rustaceans'}, {'title': 'Pythonistas'}]

This is equivalent to ``SELECT name AS title FROM band`` in SQL.

-------------------------------------------------------------------------------

Joins
-----

One of the most powerful things about ``select`` is it's support for joins.

.. code-block:: python

    >>> Band.select(Band.name, Band.manager.name).run_sync()
    [
        {'name': 'Pythonistas', 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.name': 'Graydon'}
    ]


The joins can go several layers deep.

.. code-block:: python

    >>> Concert.select(Concert.id, Concert.band_1.manager.name).run_sync()
    [{'id': 1, 'band_1.manager.name': 'Guido'}]

all_columns
~~~~~~~~~~~

If you want all of the columns from a related table you can use
``all_columns``, which is a useful shortcut which saves you from typing them
all out:

.. code-block:: python

    >>> Band.select(Band.name, Band.manager.all_columns()).run_sync()
    [
        {'name': 'Pythonistas', 'manager.id': 1, 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.id': 2, 'manager.name': 'Graydon'}
    ]


In Piccolo < 0.41.0 you had to explicitly unpack ``all_columns``. This is
equivalent to the code above:

.. code-block:: python

    >>> Band.select(Band.name, *Band.manager.all_columns()).run_sync()


You can exclude some columns if you like:

.. code-block:: python

    >>> Band.select(
    >>>     Band.name,
    >>>     Band.manager.all_columns(exclude=[Band.manager.id)
    >>> ).run_sync()
    [
        {'name': 'Pythonistas', 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.name': 'Graydon'}
    ]


Strings are supported too if you prefer:

.. code-block:: python

    >>> Band.select(
    >>>     Band.name,
    >>>     Band.manager.all_columns(exclude=['id'])
    >>> ).run_sync()
    [
        {'name': 'Pythonistas', 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'manager.name': 'Graydon'}
    ]

You can also use ``all_columns`` on the root table, which saves you time if
you have lots of columns. It works identically to related tables:

.. code-block:: python

    >>> Band.select(
    >>>     Band.all_columns(exclude=[Band.id]),
    >>>     Band.manager.all_columns(exclude=[Band.manager.id])
    >>> ).run_sync()
    [
        {'name': 'Pythonistas', 'popularity': 1000, 'manager.name': 'Guido'},
        {'name': 'Rustaceans', 'popularity': 500, 'manager.name': 'Graydon'}
    ]

Nested
~~~~~~

You can also get the response as nested dictionaries, which can be very useful:

.. code-block:: python

    >>> Band.select(Band.name, Band.manager.all_columns()).output(nested=True).run_sync()
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

    Band.select('name').run_sync()

    # For joins:
    Band.select('manager.name').run_sync()

-------------------------------------------------------------------------------

Aggregate functions
-------------------

Count
~~~~~

Returns the number of rows which match the query:

.. code-block:: python

    >>> Band.count().where(Band.name == 'Pythonistas').run_sync()
    1

Avg
~~~

Returns the average for a given column:

.. code-block:: python

    >>> from piccolo.query import Avg
    >>> response = Band.select(Avg(Band.popularity)).first().run_sync()
    >>> response["avg"]
    750.0

Sum
~~~

Returns the sum for a given column:

.. code-block:: python

    >>> from piccolo.query import Sum
    >>> response = Band.select(Sum(Band.popularity)).first().run_sync()
    >>> response["sum"]
    1500

Max
~~~

Returns the maximum for a given column:

.. code-block:: python

    >>> from piccolo.query import Max
    >>> response = Band.select(Max(Band.popularity)).first().run_sync()
    >>> response["max"]
    1000

Min
~~~

Returns the minimum for a given column:

.. code-block:: python

    >>> from piccolo.query import Min
    >>> response = Band.select(Min(Band.popularity)).first().run_sync()
    >>> response["min"]
    500

Additional features
~~~~~~~~~~~~~~~~~~~

You also can chain multiple different aggregate functions in one query:

.. code-block:: python

    >>> from piccolo.query import Avg, Sum
    >>> response = Band.select(Avg(Band.popularity), Sum(Band.popularity)).first().run_sync()
    >>> response
    {"avg": 750.0, "sum": 1500}

And can use aliases for aggregate functions like this:

.. code-block:: python

    >>> from piccolo.query import Avg
    >>> response = Band.select(Avg(Band.popularity, alias="popularity_avg")).first().run_sync()
    >>> response["popularity_avg"]
    750.0

    # Alternatively, you can use the `as_alias` method.
    >>> response = Band.select(Avg(Band.popularity).as_alias("popularity_avg")).first().run_sync()
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
    Band.select().run_sync()

To restrict the returned columns, either pass in the columns into the
``select`` method, or use the ``columns`` method.

.. code-block:: python

    # Equivalent to SELECT name from band
    Band.select(Band.name).run_sync()

    # Or alternatively:
    Band.select().columns(Band.name).run_sync()

The ``columns`` method is additive, meaning you can chain it to add additional
columns.

.. code-block:: python

    Band.select().columns(Band.name).columns(Band.manager).run_sync()

    # Or just define it one go:
    Band.select().columns(Band.name, Band.manager).run_sync()


first
~~~~~

See  :ref:`first`.

group_by
~~~~~~~~

See  :ref:`group_by`.

limit
~~~~~

See  :ref:`limit`.

offset
~~~~~~

See  :ref:`offset`.

distinct
~~~~~~~~

See  :ref:`distinct`.

order_by
~~~~~~~~

See  :ref:`order_by`.

output
~~~~~~

See :ref:`output`.

where
~~~~~

See  :ref:`where`.
