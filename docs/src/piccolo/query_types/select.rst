.. _Select:

Select
======

.. hint:: Follow along by installing Piccolo and running `piccolo playground` - see :ref:`Playground`

To get all rows:

.. code-block:: python

    >>> Band.select().run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

To get certain rows:

.. code-block:: python

    >>> Band.select().columns(Band.name).run_sync()
    [{'name': 'Rustaceans'}, {'name': 'Pythonistas'}]

Or making an alias to make it shorter:

.. code-block:: python

    >>> b = Band
    >>> b.select().columns(b.name).run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

.. hint:: All of these examples also work with async by using .run() inside coroutines - see :ref:`SyncAndAsync`.

output
------

By default, the data is returned as a list of dictionaries (where each
dictionary represents a row). This can be altered using the ``output`` method.

To return the data as a JSON string:

.. code-block:: python

    >>> b = Band
    >>> b.select().output(as_json=True).run_sync()
    '[{"name":"Pythonistas","manager":1,"popularity":1000,"id":1},{"name":"Rustaceans","manager":2,"popularity":500,"id":2}]'


columns
-------

By default all columns are returned from the queried table.

.. code-block:: python

    b = Band
    # Equivalent to SELECT * from band
    b.select().run_sync()

To restrict the returned columns, used the `columns` method.

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

Joins
-----

One of the most powerful things about select is it's support for joins.

.. code-block:: python

    b = Band
    b.select().columns(
        b.name,
        b.manager.name
    ).run_sync()


The joins can go several layers deep.

.. code-block:: python

    c = Concert
    c.select().columns(
        c.id,
        c.band_1.manager.name
    ).run_sync()

order_by
--------

See  :ref:`order_by`.

where
-----

See  :ref:`where`.
