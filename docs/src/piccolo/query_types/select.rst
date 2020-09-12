.. _Select:

Select
======

.. hint:: Follow along by installing Piccolo and running `piccolo playground run` - see :ref:`Playground`

To get all rows:

.. code-block:: python

    >>> Band.select().run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

To get certain rows:

.. code-block:: python

    >>> Band.select(Band.name).run_sync()
    [{'name': 'Rustaceans'}, {'name': 'Pythonistas'}]

Or making an alias to make it shorter:

.. code-block:: python

    >>> b = Band
    >>> b.select(b.name).run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

.. hint:: All of these examples also work with async by using .run() inside coroutines - see :ref:`SyncAndAsync`.

Joins
-----

One of the most powerful things about select is it's support for joins.

.. code-block:: python

    b = Band
    b.select(
        b.name,
        b.manager.name
    ).run_sync()


The joins can go several layers deep.

.. code-block:: python

    c = Concert
    c.select(
        c.id,
        c.band_1.manager.name
    ).run_sync()

String syntax
-------------

Alternatively, you can specify the column names using a string. The
disadvantage is you won't have tab completion, but sometimes it's more
convenient.

.. code-block:: python

    Band.select('name').run_sync()

    # For joins:
    Band.select('manager.name').run_sync()

Query clauses
-------------

batch
~~~~~~~

See :ref:`batch`.

columns
~~~~~~~

By default all columns are returned from the queried table.

.. code-block:: python

    b = Band
    # Equivalent to SELECT * from band
    b.select().run_sync()

To restrict the returned columns, either pass in the columns into the
``select`` method, or use the `columns` method.

.. code-block:: python

    b = Band
    # Equivalent to SELECT name from band
    b.select().columns(b.name).run_sync()

The `columns` method is additive, meaning you can chain it to add additional
columns.

.. code-block:: python

    b = Band
    b.select().columns(b.name).columns(b.manager).run_sync()

    # Or just define it one go:
    b.select().columns(b.name, b.manager).run_sync()


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

order_by
~~~~~~~~

See  :ref:`order_by`.

output
~~~~~~

By default, the data is returned as a list of dictionaries (where each
dictionary represents a row). This can be altered using the ``output`` method.

To return the data as a JSON string:

.. code-block:: python

    >>> b = Band
    >>> b.select().output(as_json=True).run_sync()
    '[{"name":"Pythonistas","manager":1,"popularity":1000,"id":1},{"name":"Rustaceans","manager":2,"popularity":500,"id":2}]'

Piccolo uses `orjson <https://github.com/ijl/orjson>`_ for JSON serialisation, which is blazing fast, and can handle most Python types, including dates, datetimes, and UUIDs.

where
~~~~~

See  :ref:`where`.
