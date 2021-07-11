.. _Select:

Select
======

.. hint:: Follow along by installing Piccolo and running `piccolo playground run` - see :ref:`Playground`

To get all rows:

.. code-block:: python

    >>> Band.select().run_sync()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000},
     {'id': 2, 'name': 'Rustaceans', 'manager': 2, 'popularity': 500}]

To get certain columns:

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

as_alias
--------

By using ``as_alias``, the name of the row can be overriden in the response.

.. code-block:: python

    >>> Band.select(Band.name.as_alias('title')).run_sync()
    [{'title': 'Rustaceans'}, {'title': 'Pythonistas'}]

This is equivalent to ``SELECT name AS title FROM band`` in SQL.

Joins
-----

One of the most powerful things about select is it's support for joins.

.. code-block:: python

    >>> b = Band
    >>> b.select(b.name, b.manager.name).run_sync()
    [{'name': 'Pythonistas', 'manager.name': 'Guido'}, {'name': 'Rustaceans', 'manager.name': 'Graydon'}]


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
``select`` method, or use the ``columns`` method.

.. code-block:: python

    b = Band
    # Equivalent to SELECT name from band
    b.select().columns(b.name).run_sync()

The ``columns`` method is additive, meaning you can chain it to add additional
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

See :ref:`output`.

where
~~~~~

See  :ref:`where`.
