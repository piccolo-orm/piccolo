.. _Count:

Count
=====

The ``count`` query makes it really easy to retrieve the number of rows in a
table:

.. code-block:: python

    >>> await Band.count()
    3

It's equivalent to this ``select`` query:

.. code-block:: python

    from piccolo.query.methods.select import Count

    >>> response = await Band.select(Count())
    >>> response[0]['count']
    3

As you can see, the ``count`` query is more convenient.

Non-null columns
----------------

If you want to retrieve the number of rows where a given column isn't null, we
can do so as follows:

.. code-block:: python

    await Band.count(column=Band.name)

    # Or simply:
    await Band.count(Band.name)

Note, this is equivalent to:

.. code-block:: python

    await Band.count().where(Band.name.is_not_null())

Example
~~~~~~~

If we have the following database table:

.. code-block:: python

    class Band(Table):
        name = Varchar()
        popularity = Integer(null=True)

With the following data:

.. table::
    :widths: auto

    ============ ==========
    name         popularity
    ============ ==========
    Pythonistas  1000
    Rustaceans   800
    C-Sharps     ``null``
    ============ ==========

Then we get the following results:

.. code-block:: python

    >>> await Band.count()
    3

    >>> await Band.count(Band.popularity)
    2

distinct
--------

We can count the number of distinct (i.e. unique) rows.

.. code-block:: python

    await Band.count(distinct=[Band.name])

With the following data:

.. table::
    :widths: auto

    ============ ==========
    name         popularity
    ============ ==========
    Pythonistas  1000
    Pythonistas  1000
    Pythonistas  800
    Rustaceans   800
    ============ ==========

Note how we have duplicate band names.

.. hint::
    This is bad database design as we should add a unique constraint to
    prevent this, but go with it for this example!

Let's compare queries with and without ``distinct``:

.. code-block:: python

    >>> await Band.count()
    4

    >>> await Band.count(distinct=[Band.name])
    2

We can specify multiple columns:

.. code-block:: python

    >>> await Band.count(distinct=[Band.name, Band.popularity])
    3

In the above example, this means we count rows where the combination of
``name`` and ``popularity`` is unique.

So ``('Pythonistas', 1000)`` is a distinct value from ``('Pythonistas', 800)``,
because even though the ``name`` is the same, the ``popularity`` is different.

Clauses
-------

where
~~~~~

See :ref:`where`.
