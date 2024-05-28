.. _where:

where
=====

You can use ``where`` clauses with the following queries:

* :ref:`Count`
* :ref:`Delete`
* :ref:`Exists`
* :ref:`Objects`
* :ref:`Select`
* :ref:`Update`

It allows powerful filtering of your data.

-------------------------------------------------------------------------------

Equal / Not Equal
-----------------

.. code-block:: python

    await Band.select().where(
        Band.name == 'Pythonistas'
    )

.. code-block:: python

    await Band.select().where(
        Band.name != 'Rustaceans'
    )

.. hint:: With :class:`Boolean <piccolo.columns.column_types.Boolean>` columns,
   some linters will complain if you write
   ``SomeTable.some_column == True`` (because it's more Pythonic to do
   ``is True``). To work around this, you can do
   ``SomeTable.some_column.eq(True)``. Likewise, with ``!=`` you can use
   ``SomeTable.some_column.ne(True)``

-------------------------------------------------------------------------------

Greater than / less than
------------------------

You can use the ``<, >, <=, >=`` operators, which work as you expect.

.. code-block:: python

    await Band.select().where(
        Band.popularity >= 100
    )

-------------------------------------------------------------------------------

like / ilike
-------------

The percentage operator is required to designate where the match should occur.

.. code-block:: python

    await Band.select().where(
        Band.name.like('Py%')  # Matches the start of the string
    )

    await Band.select().where(
        Band.name.like('%istas')  # Matches the end of the string
    )

    await Band.select().where(
        Band.name.like('%is%')  # Matches anywhere in the string
    )

    await Band.select().where(
        Band.name.like('Pythonistas')  # Matches the entire string
    )

``ilike`` is identical, except it's Postgres specific and case insensitive.

-------------------------------------------------------------------------------

not_like
--------

Usage is the same as ``like`` excepts it excludes matching rows.

.. code-block:: python

    await Band.select().where(
        Band.name.not_like('Py%')
    )

-------------------------------------------------------------------------------

is_in / not_in
--------------

You can get all rows with a value contained in the list:

.. code-block:: python

    await Band.select().where(
        Band.name.is_in(['Pythonistas', 'Rustaceans'])
    )

And all rows with a value not contained in the list:

.. code-block:: python

    await Band.select().where(
        Band.name.not_in(['Terrible Band', 'Awful Band'])
    )

-------------------------------------------------------------------------------

is_null / is_not_null
---------------------

These queries work, but some linters will complain about doing a comparison
with ``None``:

.. code-block:: python

    # Fetch all bands with a manager
    await Band.select().where(
        Band.manager != None
    )

    # Fetch all bands without a manager
    await Band.select().where(
        Band.manager == None
    )

To avoid the linter errors, you can use ``is_null`` and ``is_not_null``
instead.

.. code-block:: python

    # Fetch all bands with a manager
    await Band.select().where(
        Band.manager.is_not_null()
    )

    # Fetch all bands without a manager
    await Band.select().where(
        Band.manager.is_null()
    )

-------------------------------------------------------------------------------

Complex queries - and / or
---------------------------

You can make complex ``where`` queries using ``&`` for AND, and ``|`` for OR.

.. code-block:: python

    await Band.select().where(
        (Band.popularity >= 100) & (Band.popularity < 1000)
    )

    await Band.select().where(
        (Band.popularity >= 100) | (Band.name ==  'Pythonistas')
    )

You can make really complex ``where`` clauses if you so choose - just be
careful to include brackets in the correct place.

.. code-block:: python

    ((b.popularity >= 100) & (b.manager.name ==  'Guido')) | (b.popularity > 1000)

Multiple ``where`` clauses
~~~~~~~~~~~~~~~~~~~~~~~~~~

Using multiple ``where`` clauses is equivalent to an AND.

.. code-block:: python

    # These are equivalent:
    await Band.select().where(
        (Band.popularity >= 100) & (Band.popularity < 1000)
    )

    await Band.select().where(
        Band.popularity >= 100
    ).where(
        Band.popularity < 1000
    )

Also, multiple arguments inside ``where`` clause is equivalent to an AND.

.. code-block:: python

    # These are equivalent:
    await Band.select().where(
        (Band.popularity >= 100) & (Band.popularity < 1000)
    )

    await Band.select().where(
        Band.popularity >= 100, Band.popularity < 1000
    )

Using And / Or directly
~~~~~~~~~~~~~~~~~~~~~~~

Rather than using the ``|`` and ``&`` characters, you can use the ``And`` and
``Or`` classes, which are what's used under the hood.

.. code-block:: python

    from piccolo.columns.combination import And, Or

    await Band.select().where(
        Or(
            And(Band.popularity >= 100, Band.popularity < 1000),
            Band.name == 'Pythonistas'
        )
    )

-------------------------------------------------------------------------------

WhereRaw
--------

In certain situations you may want to have raw SQL in your where clause.

.. code-block:: python

    from piccolo.columns.combination import WhereRaw

    await Band.select().where(
        WhereRaw("name = 'Pythonistas'")
    )

It's important to parameterise your SQL statements if the values come from an
untrusted source, otherwise it could lead to a SQL injection attack.

.. code-block:: python

    from piccolo.columns.combination import WhereRaw

    value = "Could be dangerous"

    await Band.select().where(
        WhereRaw("name = {}", value)
    )

``WhereRaw`` can be combined into complex queries, just as you'd expect:

.. code-block:: python

    from piccolo.columns.combination import WhereRaw

    await Band.select().where(
        WhereRaw("name = 'Pythonistas'") | (Band.popularity > 1000)
    )

-------------------------------------------------------------------------------

Joins
-----

The ``where`` clause has full support for joins. For example:

.. code-block:: python

    >>> await Band.select(Band.name).where(Band.manager.name == 'Guido')
    [{'name': 'Pythonistas'}]
